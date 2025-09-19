from odoo import models, fields, _
import base64
import pandas as pd
from odoo.exceptions import ValidationError
import io
from collections import Counter


class ImportVendorPricelist(models.Model):
    _name = 'import.vendor.pricelist'

    upload_vendor_pricelist_file = fields.Binary('File', required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)

    def convert_to_df(self):
        """Convert the uploaded CSV file to a pandas DataFrame with validations."""
        if not self.upload_vendor_pricelist_file:
            raise ValidationError(_("Please upload a vendor pricelist file."))

        try:
            decoded_file = base64.decodebytes(self.upload_vendor_pricelist_file)
            file_stream = io.BytesIO(decoded_file)
            df = pd.read_csv(file_stream).fillna(False)
        except Exception as e:
            raise ValidationError(_("The uploaded file is invalid or not a CSV format."))

        required_columns = ["Model", "Config"]
        if not all(col in df.columns for col in required_columns):
            raise ValidationError(
                _("The uploaded file must contain the following columns: %s" % ", ".join(required_columns))
            )
        return df

    def import_pricelist(self):
        """Import vendor pricelist from the uploaded file with validations."""
        df = self.convert_to_df()
        df.columns = ["Model", "Config", "BLT", "BLJ", "SKA", "HON", "QUE", "BMO", "BVP", "ANP", "NCP", "TOP",
                      "VOP/BRP", "NPP", "NNP", "SKP/PEP", "BVS", "ANS", "NCS", "TOS", "VOS/BRS", "BV", "AN/NW", "NC",
                      "TO", "VO/BR", "NP/OH", "NN", "SK/PE", "BV+FAB", "AN+FAB", "NC+FAB"]

        column_names = df.columns[2:]  # Columns containing price data
        products_not_found = []

        # Validate that a company is selected
        if not self.company_id:
            raise ValidationError(_("Please select a company before importing."))

        # Search for the partner based on the customer code and name
        partner = self.env['res.partner'].search(
            [('customer_code', '=', 'C00029'), ('name', '=', 'Newcentury Trading (India) Private Ltd-HO*')]
        )
        if not partner:
            raise ValidationError(_("The required partner does not exist in the system."))

        # Process each row in the CSV file
        for _, row in df.iterrows():
            product_name = row['Model']
            config = row['Config']
            if not config:
                continue  # Skip rows without a configuration

            # Search for the product variant based on model name and configuration
            product_id = self.env['product.product'].search([('name', '=', product_name)]).filtered(
                lambda x: config.strip() in x.product_template_attribute_value_ids.mapped('name')
            )

            if not product_id:
                # Log products not found for future reporting
                products_not_found.append({'Model': product_name, 'Config': config})
                continue

            # Process each pricing column
            for col_name in column_names:
                price = row.get(col_name, 0)
                if not price:
                    continue  # Skip empty prices

                # Search for the product variant corresponding to the price column
                product_variant = product_id.filtered(
                    lambda x: col_name.strip() in x.product_template_attribute_value_ids.mapped('name')
                )
                if not product_variant:
                    # Raise error with detailed message including Config and Variant (col_name)
                    raise ValidationError(
                        f"Variant '{col_name}' not created for Product '{product_name}' with Config '{config}'."
                    )

                # Create or update the pricelist entry for the variant
                self._create_or_update_pricelist(product_variant, partner, price)

        # Raise error if any products were not found
        if products_not_found:
            error_message = "Products not found:\n" + "\n".join(
                [f"- Model: {p['Model']}, Config: {p['Config']}" for p in products_not_found]
            )
            raise ValidationError(error_message)

        return {
            'effect': {
                'fadeout': 'slow',
                'type': 'rainbow_man',
                'message': "Price List Imported Successfully!"
            }
        }


    def _create_or_update_pricelist(self, product_variants, partner, price):
        """Create or update vendor pricelists and show all duplicate products at once."""

        # Detect duplicate products by name
        seen = set()
        duplicates = []

        for product_variant in product_variants:
            product_name = product_variant.name
            if product_name in seen:
                if product_name not in duplicates:
                    duplicates.append(product_name)
            else:
                seen.add(product_name)

        if duplicates:
            duplicate_message = ', '.join(duplicates)
            raise ValidationError(
                _("Duplicate products found: %s.")
                % duplicate_message
            )

        # Ensure price is a float
        if isinstance(price, str):
            price = float(price.strip().replace(',', ''))
        elif isinstance(price, int):
            price = float(price)
        elif not isinstance(price, (int, float)):
            raise ValidationError(_("Invalid price format."))

        # Process each product individually
        for product_variant in product_variants:
            create_pricelist = {
                'partner_id': partner.id,
                'product_tmpl_id': product_variant.product_tmpl_id.id,
                'product_id': product_variant.id,
                'min_qty': 1,
                'price': price,
                'company_id': self.company_id.id,
            }

            # Check if the variant exists
            variant_found = False
            for col_name in product_variant.product_template_attribute_value_ids.mapped('name'):
                if col_name.strip() in product_variant.product_template_attribute_value_ids.mapped('name'):
                    variant_found = True
                    break

            if not variant_found:
                raise ValidationError(
                    _("Variant not created: %s for Product: %s, Config: %s")
                    % (col_name, product_variant.name, product_variant.product_tmpl_id.name)
                )

            # Search for existing pricelists
            search_price_list = self.env['product.supplierinfo'].search([
                ('partner_id', '=', partner.id),
                ('product_tmpl_id', '=', product_variant.product_tmpl_id.id),
                ('product_id', '=', product_variant.id),
                ('company_id', '=', self.company_id.id),
            ])

            if search_price_list:
                if len(search_price_list) > 1:
                    search_price_list.unlink()
                search_price_list.write({'price': price})
            else:
                self.env['product.supplierinfo'].create(create_pricelist)
