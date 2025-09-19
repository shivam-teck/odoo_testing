from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_amount, format_date, formatLang, get_lang, groupby



class InheritPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    additional_discount = fields.Float('Additional Discount')
    is_case_good = fields.Boolean(related='product_id.is_case_good')
    article1 = fields.Many2one('material.master', string="Article 1")
    articletype_2 = fields.Many2one('material.master', string="Article 2")
    price_unit = fields.Float(
        string='Unit Price', required=True, digits='Product Price',
        compute="_compute_price_unit_and_date_planned_and_name", readonly=False, store=True)
    product_location_type = fields.Selection([('mts', 'MTS'), ('mto', 'MTO'), ('floor', 'Floor Piece')])
    route = fields.Char('Route')
    route_id = fields.Many2one('stock.route', string='Route', domain=[('sale_selectable', '=', True)], ondelete='restrict', check_company=True,required=True)

    @api.onchange('route_id')
    def _l10n_cl_onchange_journal(self):
        self.route = self.route_id.name



    # @api.depends('product_qty', 'product_uom', 'product_id')
    # def _compute_price_unit_and_date_planned_and_name(self):
    #     pricelist = self.env['product.pricelist'].search([('is_default_pricelist', '=', True)])
    #     for line in self:
    #         if not line.product_id or line.invoice_lines:
    #             continue
    #         params = {'order_id': line.order_id}
    #         seller = line.product_id._select_seller(
    #             partner_id=line.partner_id,
    #             quantity=line.product_qty,
    #             date=line.order_id.date_order and line.order_id.date_order.date(),
    #             uom_id=line.product_uom,
    #             params=params)
    #
    #         if seller or not line.date_planned:
    #             line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #
    #         # If not seller, use the standard price. It needs a proper currency conversion.
    #         if not seller:
    #             unavailable_seller = line.product_id.seller_ids.filtered(
    #                 lambda s: s.partner_id == line.order_id.partner_id)
    #             if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
    #                 # Avoid to modify the price unit if there is no price list for this partner and
    #                 # the line has already one to avoid to override unit price set manually.
    #                 continue
    #             po_line_uom = line.product_uom or line.product_id.uom_po_id
    #             price_unit = line.env['account.tax']._fix_tax_included_price_company(
    #                 line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
    #                 line.product_id.supplier_taxes_id,
    #                 line.taxes_id,
    #                 line.company_id,
    #             )
    #             price_unit = line.product_id.currency_id._convert(
    #                 price_unit,
    #                 line.currency_id,
    #                 line.company_id,
    #                 line.date_order,
    #                 False
    #             )
    #             # line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
    #             #                                                                self.env[
    #             #                                                                    'decimal.precision'].precision_get(
    #             #                                                                    'Product Price')))
    #             margin = self.env['franchise.margin'].search(
    #                 [('company', '=', line.company_id.id), ('product_category', '=', line.product_id.categ_id.id)])
    #             print(margin,'marginn')
    #             if margin and self.company_id.apply_vendor_pricelist == False:
    #                 if line.order_id.origin:
    #                     price_unit = line.product_id.lst_price
    #                     margin_price = price_unit * margin.margin_rate / 100
    #                     price_unit_margin = price_unit - margin_price
    #                     # rec['price_unit'] = price_unit_margin
    #                     line.price_unit = price_unit_margin
    #                 else:
    #                     price_unit = line.product_id.lst_price
    #                     margin_price = price_unit * margin.margin_rate / 100
    #                     price_unit_margin = price_unit - margin_price
    #                     for item in pricelist.item_ids:
    #                         print(item.product_id.id, 'variant')
    #                         print(item.product_tmpl_id.id, 'product')
    #                         if item.product_id.id == line.product_id.id:
    #                             discount_price = price_unit_margin * item.percent_price / 100
    #                             final_price = price_unit_margin - discount_price
    #                             line.price_unit = final_price
    #                             break
    #                         elif item.product_tmpl_id.id == line.product_id.product_tmpl_id.id:
    #                             discount_price = price_unit_margin * item.percent_price / 100
    #                             final_price = price_unit_margin - discount_price
    #                             line.price_unit = final_price
    #                             break
    #                         elif item.categ_id.id == line.product_id.product_tmpl_id.categ_id.id:
    #                             discount_price = price_unit_margin * item.percent_price / 100
    #                             final_price = price_unit_margin - discount_price
    #                             line.price_unit = final_price
    #                             break
    #                         elif item.name == 'All Products':
    #                             discount_price = price_unit_margin * item.percent_price / 100
    #                             final_price = price_unit_margin - discount_price
    #                             line.price_unit = final_price
    #                             break
    #                         else:
    #                             line.price_unit = line.product_id.lst_price
    #                             # raise UserError("Discount is missing in Pricelist")
    #
    #             elif not margin and self.company_id.business_type != 'ho':
    #                 raise UserError("Margin is missing")
    #
    #             continue
    #
    #         price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price,
    #                                                                              line.product_id.supplier_taxes_id,
    #                                                                              line.taxes_id,
    #                                                                              line.company_id) if seller else 0.0
    #         price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order,
    #                                                  False)
    #         price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
    #                                                                   self.env['decimal.precision'].precision_get(
    #                                                                       'Product Price')))
    #         # line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)
    #         margin = self.env['franchise.margin'].search(
    #             [('company', '=', line.company_id.id), ('product_category', '=', line.product_id.categ_id.id)])
    #         if margin and self.company_id.apply_vendor_pricelist == False:
    #             if line.order_id.origin:
    #                 price_unit = line.product_id.lst_price
    #                 margin_price = price_unit * margin.margin_rate / 100
    #                 price_unit_margin = price_unit - margin_price
    #                 # rec['price_unit'] = price_unit_margin
    #                 line.price_unit = price_unit_margin
    #             else:
    #                 price_unit = line.product_id.lst_price
    #                 margin_price = price_unit * margin.margin_rate / 100
    #                 price_unit_margin = price_unit - margin_price
    #                 for item in pricelist.item_ids:
    #                     print(item.product_id.id,'variant')
    #                     print(item.product_tmpl_id.id,'product')
    #                     if item.product_id.id == line.product_id.id:
    #                         discount_price = price_unit_margin * item.percent_price / 100
    #                         final_price = price_unit_margin - discount_price
    #                         line.price_unit = final_price
    #                         break
    #                     elif item.product_tmpl_id.id == line.product_id.product_tmpl_id.id:
    #                         discount_price = price_unit_margin * item.percent_price / 100
    #                         final_price = price_unit_margin - discount_price
    #                         line.price_unit = final_price
    #                         break
    #                     elif item.categ_id.id == line.product_id.product_tmpl_id.categ_id.id:
    #                         discount_price = price_unit_margin * item.percent_price / 100
    #                         final_price = price_unit_margin - discount_price
    #                         line.price_unit = final_price
    #                         break
    #                     elif item.name == 'All Products':
    #                         discount_price = price_unit_margin * item.percent_price / 100
    #                         final_price = price_unit_margin - discount_price
    #                         line.price_unit = final_price
    #                         break
    #                     else:
    #                         line.price_unit = line.product_id.lst_price
    #                         # raise UserError("Discount is missing in Pricelist")
    #
    #         elif not margin and self.company_id.business_type != 'ho':
    #             raise UserError("Margin is missing")
    #
    #         # record product names to avoid resetting custom descriptions
    #         default_names = []
    #         vendors = line.product_id._prepare_sellers({})
    #         for vendor in vendors:
    #             product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
    #             default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
    #         if not line.name or line.name in default_names:
    #             product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
    #             line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        pricelist = self.env['product.pricelist'].search([('is_default_pricelist', '=', True)])
        for line in self:
            if not line.product_id or line.invoice_lines or not line.company_id:
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(line),
                uom_id=line.product_uom,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not seller:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                po_line_uom = line.product_uom or line.product_id.uom_po_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.taxes_id,
                    line.company_id,
                )
                price_unit = line.product_id.cost_currency_id._convert(
                    price_unit,
                    line.currency_id,
                    line.company_id,
                    line.date_order or fields.Date.context_today(line),
                    False
                )
                line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                               self.env[
                                                                                   'decimal.precision'].precision_get(
                                                                                   'Product Price')))
                continue

            price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                 line.product_id.supplier_taxes_id,
                                                                                 line.taxes_id,
                                                                                 line.company_id) if seller else 0.0
            price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id,
                                                     line.date_order or fields.Date.context_today(line), False)
            price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                      self.env['decimal.precision'].precision_get(
                                                                          'Product Price')))
            line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)

            margin = self.env['franchise.margin'].search(
                [('company', '=', line.company_id.id), ('product_category', '=', line.product_id.categ_id.id)])
            if margin and self.company_id.apply_vendor_pricelist == False:
                if line.order_id.origin:
                    price_unit = line.product_id.lst_price
                    margin_price = price_unit * margin.margin_rate / 100
                    price_unit_margin = price_unit - margin_price
                    # rec['price_unit'] = price_unit_margin
                    line.price_unit = price_unit_margin
                else:
                    price_unit = line.product_id.lst_price
                    margin_price = price_unit * margin.margin_rate / 100
                    price_unit_margin = price_unit - margin_price
                    for item in pricelist.item_ids:
                        print(item.product_id.id, 'variant')
                        print(item.product_tmpl_id.id, 'product')
                        if item.product_id.id == line.product_id.id:
                            discount_price = price_unit_margin * item.percent_price / 100
                            final_price = price_unit_margin - discount_price
                            line.price_unit = final_price
                            break
                        elif item.product_tmpl_id.id == line.product_id.product_tmpl_id.id:
                            discount_price = price_unit_margin * item.percent_price / 100
                            final_price = price_unit_margin - discount_price
                            line.price_unit = final_price
                            break
                        elif item.categ_id.id == line.product_id.product_tmpl_id.categ_id.id:
                            discount_price = price_unit_margin * item.percent_price / 100
                            final_price = price_unit_margin - discount_price
                            line.price_unit = final_price
                            break
                        elif item.name == 'All Products':
                            discount_price = price_unit_margin * item.percent_price / 100
                            final_price = price_unit_margin - discount_price
                            line.price_unit = final_price
                            break
                        else:
                            line.price_unit = line.product_id.lst_price

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))


class InheritPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    oc_no = fields.Char('OC Number')



    @api.model_create_multi
    def create(self, vals_list):
        orders = self.browse()
        partner_vals_list = []
        for vals in vals_list:
            company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
            # Ensures default picking type and currency are taken from the right company.
            self_comp = self.with_company(company_id)
            if vals.get('name', 'New') == 'New':
                seq_date = None
                if 'date_order' in vals:
                    seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase.order',
                                                                         sequence_date=seq_date) or '/'
            vals, partner_vals = self._write_partner_values(vals)
            partner_vals_list.append(partner_vals)
            orders |= super(InheritPurchaseOrder, self_comp).create(vals)
            # if vals.get('origin'):
            #     orders.button_confirm()

        for order, partner_vals in zip(orders, partner_vals_list):
            if partner_vals:
                order.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
        return orders



    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        """ Generate the Sales Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
        """

        # it may not affected because of parallel company relation
        price = line.price_unit or 0.0
        quantity = line.product_id and line.product_uom._compute_quantity(line.product_qty,
                                                                          line.product_id.uom_id) or line.product_qty
        price = line.product_id and line.product_uom._compute_price(price, line.product_id.uom_id) or price
        return {
            'name': line.name,
            'product_uom_qty': quantity,
            'product_id': line.product_id and line.product_id.id or False,
            'article1': line.article1.id,
            'articletype_2': line.articletype_2.id,
            'product_uom': line.product_id and line.product_id.uom_id.id or line.product_uom.id,
            'price_unit': price,
            'customer_lead': line.product_id and line.product_id.sale_delay or 0.0,
            'company_id': company.id,
            'display_type': line.display_type,
            'route': line.route if line.route else False
            # 'product_location_type': line.product_location_type if line.product_location_type else False,
        }
