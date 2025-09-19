from itertools import groupby
from psycopg2 import sql
from odoo import _, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        uom_id = vals.pop("uom_id", False)
        uom_po_id = vals.pop("uom_po_id", False)

        warning_shown = False

        if uom_id:
            warning_shown = self._update_uom_and_related_models(uom_id, "uom_id", warning_shown)
        if uom_po_id:
            self._update_uom_and_related_models(uom_po_id, "uom_po_id", warning_shown)

        return super().write(vals)

    def _update_uom_and_related_models(self, new_uom_id, field_name, warning_shown):
        """ Update UoM for product.template and its related models in a single transaction. """
        uom_obj = self.env["uom.uom"]
        new_uom = uom_obj.browse(new_uom_id)

        sorted_items = sorted(self, key=lambda r: r[field_name])

        category_mismatch = False  # Track if there's a category mismatch

        for key, products_group in groupby(sorted_items, key=lambda r: r[field_name]):
            product_ids = [p.id for p in products_group]

            if key.category_id != new_uom.category_id:
                category_mismatch = True

            queries = [
                sql.SQL("UPDATE product_template SET {field} = %s WHERE id in %s").format(
                    field=sql.Identifier(field_name)
                )
            ]
            params = [(new_uom.id, tuple(product_ids))]

            related_models = {
                "stock.move": "product_uom",
                "stock.move.line": "product_uom_id",
                "sale.order.line": "product_uom",
                "purchase.order.line": "product_uom",
                "mrp.bom": "product_uom_id",
                "mrp.production": "product_uom_id",
            }

            installed_models = self.env["ir.model"].search([]).mapped("model")
            variant_ids = tuple(self.mapped("product_variant_ids").ids)

            for model, field in related_models.items():
                if model in installed_models and variant_ids:
                    queries.append(
                        sql.SQL("UPDATE {table} SET {field} = %s WHERE product_id IN %s").format(
                            table=sql.Identifier(model.replace(".", "_")),
                            field=sql.Identifier(field),
                        )
                    )
                    params.append((new_uom.id, variant_ids))

            for query, param in zip(queries, params):
                self.env.cr.execute(query, param)

            self.env["product.template"].browse(product_ids).invalidate_recordset(fnames=[field_name])
            for model, field in related_models.items():
                if model in installed_models:
                    self.env[model].invalidate_recordset(fnames=[field])

        if category_mismatch and not warning_shown:
            self.message_post(
                body=_(
                    "⚠️ WARNING: UNIT OF MEASURE CATEGORY MISMATCH!\n"
                    "The selected Unit of Measure belongs to a DIFFERENT CATEGORY than the current one.\n"
                    "✅ The update has been applied successfully.\n"
                    "🔍 Please verify this change to ensure it does not affect inventory calculations or transactions."
                )
            )

        return warning_shown or category_mismatch