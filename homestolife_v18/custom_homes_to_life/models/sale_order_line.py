from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class InheritSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    mrp_price = fields.Float(related='product_id.mrp_price', string='MRP')
    is_case_good = fields.Boolean(related='product_template_id.is_case_good')
    article1 = fields.Many2one('material.master', string="Article 1")
    articletype_2 = fields.Many2one('material.master', string="Article 2")
    additional_discount = fields.Float('Additional Discount', digits=(12, 4), compute='compute_additional_disc')
    customer_phone_no = fields.Char(related='order_id.partner_id.phone')
    view_discount = fields.Float('Discount', compute='compute_view_discount', digits=(12, 4), readonly=True)
    discount = fields.Float(
        string="Discount (%)",
        # compute='_compute_discount',
        # digits='Discount',
        digits=(12, 4),
        store=True, readonly=False, precompute=True)
    help_desk_id = fields.Many2one('helpdesk.ticket')
    product_location_type = fields.Selection([('mts', 'MTS'), ('mto', 'MTO'), ('floor', 'Floor Piece')], required=False)
    route_id = fields.Many2one('stock.route', string='Route', domain=[('sale_selectable', '=', True)],
                               ondelete='restrict', check_company=True)
    route = fields.Char('PO Route', readonly=True)

    is_ho_account = fields.Boolean('HO account', default=lambda self: self._default_check_ho())

    company_type = fields.Selection(related='order_id.company_id.business_type')

    # view_price_unit = fields.Float(string="Unit Price", compute='compute_view_price_unit')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self._default_company())


    def compute_view_price_unit(self):
        for rec in self:
            rec.view_price_unit = rec.price_unit

    def _default_company(self):
        company = self.env.company.id
        return company

    def _default_check_ho(self):
        is_ho = False if self.env.company.business_type == 'ho' else True
        return is_ho

    # @api.depends('discount')
    # def compute_ho_account(self):
    #     for rec in self:
    #         if rec.order_id.company_id.business_type == 'ho':
    #             rec.is_ho_account = True
    #         else:
    #             rec.is_ho_account = False

    @api.depends('discount')
    def compute_view_discount(self):
        for rec in self:
            rec.view_discount = rec.discount

    @api.depends('product_id')
    def _compute_price_unit(self):
        for line in self:
            line.price_unit = line.product_id.lst_price

    # @api.model
    # def create(self, vals):
    #     if vals.get('product_id.detailed_type') == 'service':
    #         print('yes')
    #         # vals.get('discount') == 0.0
    #     res = super(InheritSaleOrderLine, self).create(vals)
    #     return res

    @api.depends('discount', 'product_id', 'product_uom', 'product_uom_qty')
    def compute_additional_disc(self):
        for line in self:
            if line.product_id.type == 'service':
                # line.product_id.is_case_good = True
                line.additional_discount = 0.0
                line.discount = 0.0
                continue
            if not line.product_id or line.display_type:
                line.discount = 0.0
            # if not (line.order_id.pricelist_id and line.order_id.pricelist_id.discount_policy == 'without_discount'):
            #     line.additional_discount = 0.0
            #     continue

            # line.discount = 0.0

            if not line.pricelist_item_id:
                line.additional_discount = 0.0
                # No pricelist rule was found for the product
                # therefore, the pricelist didn't apply any discount/change
                # to the existing sales price.

                continue

            initial_discount = 0.0
            line = line.with_company(line.company_id)
            pricelist_price = line._get_pricelist_price()
            base_price = line._get_pricelist_price_before_discount()
            if base_price != 0:  # Avoid division by zero
                discount = (base_price - pricelist_price) / base_price * 100
                if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
                    discount_value = round(discount / 100, 4)
                    initial_discount = line.price_unit * discount_value
                    total_disc = line.price_unit * (line.discount / 100)
                    line.additional_discount = total_disc - initial_discount
                else:
                    line.additional_discount = 0.0
            else:
                line.additional_discount = 0.0

    # @api.depends('product_id', 'product_uom', 'product_uom_qty', 'additional_discount')
    # def _compute_discount(self):
    #     for line in self:
    #         if not line.product_id or line.display_type:
    #             line.discount = 0.0
    #
    #         if not (
    #                 line.order_id.pricelist_id
    #                 and line.order_id.pricelist_id.discount_policy == 'without_discount'
    #         ):
    #             continue
    #
    #         line.discount = 0.0
    #
    #         if not line.pricelist_item_id:
    #             # No pricelist rule was found for the product
    #             # therefore, the pricelist didn't apply any discount/change
    #             # to the existing sales price.
    #             continue
    #
    #         line = line.with_company(line.company_id)
    #         pricelist_price = line._get_pricelist_price()
    #         base_price = line._get_pricelist_price_before_discount()
    #
    #         if base_price != 0:  # Avoid division by zero
    #             discount = (base_price - pricelist_price) / base_price * 100
    #             if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
    #                 # only show negative discounts if price is negative
    #                 # otherwise it's a surcharge which shouldn't be shown to the customer
    #                 additional_discount = round(
    #                     ((line.additional_discount / (line.price_unit * line.product_uom_qty)) * 100), 3)
    #
    #                 # print(additional_discount, 'rounded value')
    #                 disc = discount + additional_discount
    #                 line.discount = round(disc, 4)
    #                 print(line.discount, 'discount line round')

    def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.
        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [Command.set(self.tax_id.ids)],
            'analytic_distribution': self.analytic_distribution,
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
            'additional_discount': self.additional_discount,
        }
        self._set_analytic_distribution(res, **optional_values)
        downpayment_lines = self.invoice_lines.filtered('is_downpayment')
        if self.is_downpayment and downpayment_lines:
            res['account_id'] = downpayment_lines.account_id[:1].id
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res

