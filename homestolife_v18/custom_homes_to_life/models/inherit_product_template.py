from odoo import models, api, fields, _


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    def compute_vendors(self):
        serach_partner = self.env['res.partner'].search([('name', '=', 'Newcentury Trading India Pvt Ltd-Office')])
        new_partner = self.env['res.partner'].search([('name', '=', 'Newcentury Trading (India) Private Ltd-HO')])
        search_product = self.env['product.template'].search([])
        for rec in search_product:
            if not rec.seller_ids:
                list = []
                info = (0, 0, {
                    'partner_id': new_partner.id
                })
                list.append(info)
                rec.write({'seller_ids':list})
                # for i in rec.seller_ids:
                #     if i.partner_id.id == serach_partner.id:
                #         i.partner_id = new_partner

    def set_gst_18_tax(self):
        """Set the sales and purchase tax to GST 18%"""
        sale_tax = self.env['account.tax'].search([('name', '=', 'GST 18%S')], limit=1)
        purchase_tax = self.env['account.tax'].search([('name', '=', 'GST 18%P')], limit=1)

        if not sale_tax or not purchase_tax:
            raise ValueError(_("GST 18%S or GST 18%P tax not found in system."))

        for product in self:
            product.taxes_id = [(6, 0, [sale_tax.id])]
            product.supplier_taxes_id = [(6, 0, [purchase_tax.id])]

    # def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False,
    #                           parent_combination=False, only_template=False):
    #     """ Return info about a given combination.
    #
    #     Note: this method does not take into account whether the combination is
    #     actually possible.
    #
    #     :param combination: recordset of `product.template.attribute.value`
    #
    #     :param product_id: id of a `product.product`. If no `combination`
    #         is set, the method will try to load the variant `product_id` if
    #         it exists instead of finding a variant based on the combination.
    #
    #         If there is no combination, that means we definitely want a
    #         variant and not something that will have no_variant set.
    #
    #     :param add_qty: float with the quantity for which to get the info,
    #         indeed some pricelist rules might depend on it.
    #
    #     :param pricelist: `product.pricelist` the pricelist to use
    #         (can be none, eg. from SO if no partner and no pricelist selected)
    #
    #     :param parent_combination: if no combination and no product_id are
    #         given, it will try to find the first possible combination, taking
    #         into account parent_combination (if set) for the exclusion rules.
    #
    #     :param only_template: boolean, if set to True, get the info for the
    #         template only: ignore combination and don't try to find variant
    #
    #     :return: dict with product/combination info:
    #
    #         - product_id: the variant id matching the combination (if it exists)
    #
    #         - product_template_id: the current template id
    #
    #         - display_name: the name of the combination
    #
    #         - price: the computed price of the combination, take the catalog
    #             price if no pricelist is given
    #
    #         - list_price: the catalog price of the combination, but this is
    #             not the "real" list_price, it has price_extra included (so
    #             it's actually more closely related to `lst_price`), and it
    #             is converted to the pricelist currency (if given)
    #
    #         - has_discounted_price: True if the pricelist discount policy says
    #             the price does not include the discount and there is actually a
    #             discount applied (price < list_price), else False
    #     """
    #     self.ensure_one()
    #     # get the name before the change of context to benefit from prefetch
    #     display_name = self.display_name
    #
    #     display_image = True
    #     quantity = self.env.context.get('quantity', add_qty)
    #     product_template = self
    #
    #     combination = combination or product_template.env['product.template.attribute.value']
    #
    #     if not product_id and not combination and not only_template:
    #         combination = product_template._get_first_possible_combination(parent_combination)
    #
    #     if only_template:
    #         product = product_template.env['product.product']
    #     elif product_id and not combination:
    #         product = product_template.env['product.product'].browse(product_id)
    #     else:
    #         product = product_template._get_variant_for_combination(combination)
    #
    #     if product:
    #         # We need to add the price_extra for the attributes that are not
    #         # in the variant, typically those of type no_variant, but it is
    #         # possible that a no_variant attribute is still in a variant if
    #         # the type of the attribute has been changed after creation.
    #         no_variant_attributes_price_extra = [
    #             ptav.price_extra for ptav in combination.filtered(
    #                 lambda ptav:
    #                 ptav.price_extra and
    #                 ptav not in product.product_template_attribute_value_ids
    #             )
    #         ]
    #         if no_variant_attributes_price_extra:
    #             product = product.with_context(
    #                 no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
    #             )
    #         list_price = product.price_compute('list_price')[product.id]
    #         if pricelist:
    #             price = pricelist._get_product_price(product, quantity)
    #         else:
    #             price = list_price
    #         display_image = bool(product.image_128)
    #         display_name = product.display_name
    #         price_extra = (product.price_extra or 0.0) + (sum(no_variant_attributes_price_extra) or 0.0)
    #     else:
    #         current_attributes_price_extra = [v.price_extra or 0.0 for v in combination]
    #         product_template = product_template.with_context(
    #             current_attributes_price_extra=current_attributes_price_extra)
    #         price_extra = sum(current_attributes_price_extra)
    #         list_price = product_template.price_compute('list_price')[product_template.id]
    #         if pricelist:
    #             price = pricelist._get_product_price(product_template, quantity)
    #         else:
    #             price = list_price
    #         display_image = bool(product_template.image_128)
    #
    #         combination_name = combination._get_combination_name()
    #         if combination_name:
    #             display_name = "%s (%s)" % (display_name, combination_name)
    #
    #     if pricelist and pricelist.currency_id != product_template.currency_id:
    #         list_price = product_template.currency_id._convert(
    #             list_price, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
    #             fields.Date.today()
    #         )
    #         price_extra = product_template.currency_id._convert(
    #             price_extra, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
    #             fields.Date.today()
    #         )
    #
    #     price_without_discount = list_price if pricelist and pricelist.discount_policy == 'without_discount' else price
    #     has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount,
    #                                                                                        price) == 1
    #
    #
    #     return {
    #         'product_id': product.id,
    #         'product_template_id': product_template.id,
    #         'display_name': display_name,
    #         'display_image': display_image,
    #         'price': product.lst_price,
    #         'list_price': product.lst_price,
    #         'price_extra': product.lst_price,
    #         'has_discounted_price': has_discounted_price,
    #     }
