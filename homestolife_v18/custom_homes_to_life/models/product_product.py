from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class InheritProductProduct(models.Model):
    _inherit = 'product.product'

    mrp_price = fields.Float(string='MRP Price', compute='compute_mrp')
    material_number = fields.Char(related='product_tmpl_id.material_number')
    material_description = fields.Char(related='product_tmpl_id.material_description')
    default_code = fields.Char('Internal Reference', index=True, readonly=False,tracking=True)

    price = fields.Float('Price', digits='Product Price')
    lst_price = fields.Float('Sales Price', digits='Product Price', store=True,tracking=True,
                             help="The sale price is managed from the product template. Click on the 'Configure Variants' button to set the extra attribute prices.")
    goods_type = fields.Many2one(related='product_tmpl_id.goods_type')


    @api.depends('lst_price')
    def compute_mrp(self):
        for rec in self:
            if rec.lst_price > 1:
                rec.mrp_price = rec.lst_price * 1.18
            else:
                rec.mrp_price = 0.0

    def price_compute(self, price_type, uom=False, currency=False, company=None, date=False):
        date = date or fields.Date.context_today(self)

        # TDE FIXME: delegate to template or not ? fields are reencoded here ...
        # compatibility about context keys used a bit everywhere in the code
        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])

        products = self
        if price_type == 'standard_price':
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            products = self.with_company(company or self.env.company).sudo()

        prices = dict.fromkeys(self.ids, 0.0)
        for product in products:
            prices[product.id] = product[price_type] or 0.0
            if price_type == 'list_price':
                prices[product.id] += product.lst_price
                # we need to add the price from the attributes that do not generate variants
                # (see field product.attribute create_variant)
                if self._context.get('no_variant_attributes_price_extra'):
                    # we have a list of price_extra that comes from the attribute values, we need to sum all that
                    prices[product.id] += sum(self._context.get('no_variant_attributes_price_extra'))

            if uom:
                prices[product.id] = product.uom_id._compute_price(prices[product.id], uom)

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency, product.company_id, fields.Date.today())

        return prices

    # @api.multi
    # def compute_field_visibility(self):
    #     if self.env.user.has_group('custom_homes_to_life.group_access_product_import'):
    #         self.lst_price = True

    @api.depends('list_price', 'price_extra')
    @api.depends_context('uom')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        # for product in self:
        #     if to_uom:
        #         list_price = product.uom_id._compute_price(product.list_price, to_uom)
        #     else:
        #         list_price = product.list_price
        #     product.lst_price = list_price + product.price_extra

    @api.onchange('lst_price')
    def _set_product_lst_price(self):
        pass
        # for product in self:
        #     if self._context.get('uom'):
        #         value = self.env['uom.uom'].browse(self._context['uom'])._compute_price(product.lst_price, product.uom_id)
        #         product.write({'lst_price': value})
        # else:
        #     value = product.lst_price
        # value -= product.price_extra
        # product.write({'lst_price': value})

    # def write(self, vals):
    #     vals.update({'lst_price': vals.get("lst_price")})
    #     res = super(InheritProductProduct, self).write(vals)
    #
    #     return res


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    mrp_price = fields.Float(string='MRP Price', tracking=True)
    price = fields.Float('Price', digits='Product Price', tracking=True)
    last_update = fields.Date(struct='Last Update', tracking=True)
    is_case_good = fields.Boolean(string='Is Case Good', default=False)
    material_number = fields.Char(string='SAP Material Number', tracking=True)
    material_description = fields.Char(string='Material Description', tracking=True)
    goods_type = fields.Many2one('franchise.product.category')
    variant_count = fields.Integer('Variant Count', compute='compute_variant_count')
    internal_reference = fields.Char(string='Internal Reference Variants', tracking=True)
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True, tracking=True)

    @api.model
    def create(self, vals):
        # Check if a product with the same name already exists
        product_name = vals.get('name')
        product_type = vals.get('detailed_type')
        # print(product_type)
        existing_product = self.env['product.product'].search([('name', '=', product_name)])

        if existing_product and product_type != 'service':
            raise ValidationError('A product with this name already exists.')

        # Call the original create method to create the product
        return super(InheritProductTemplate, self).create(vals)

    # compute_internal reference
    def compute_default_code(self):
        for rec in self:
            search_products = self.env['product.product'].search([('product_tmpl_id','=',rec.id)])
            if search_products:
                for prd in search_products:
                    prd.default_code = rec.internal_reference

    # count variant
    @api.depends('product_variant_count')
    def compute_variant_count(self):
        for rec in self:
            if rec.product_variant_count:
                rec.variant_count = rec.product_variant_count
            else:
                rec.variant_count = 0


    # for adding taxes
    @api.depends('company_id')
    def _compute_all_companies_selected(self):
        for rec in self:
            search_company = self.env['res.company'].search([])
            selected_companies = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
            if len(search_company) == len(selected_companies):
                rec.is_all_companies_selected = True
            else:
                rec.is_all_companies_selected = False


    is_all_companies_selected = fields.Boolean("All Companies Selected", compute='_compute_all_companies_selected',
                                               store=False)

    def update_taxes(self):
        for rec in self:
            selected_companies = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
            sale_tax = []
            purchase_tax = []
            for comp in selected_companies:
                sale_tax.append(comp.account_sale_tax_id.id)
                purchase_tax.append(comp.account_purchase_tax_id.id)
            rec.taxes_id = [(6, 0, sale_tax)]
            rec.supplier_taxes_id = [(6, 0, purchase_tax)]





    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False,
                              parent_combination=False, only_template=False):
        """ Return info about a given combination.

        Note: this method does not take into account whether the combination is
        actually possible.

        :param combination: recordset of `product.template.attribute.value`

        :param product_id: id of a `product.product`. If no `combination`
            is set, the method will try to load the variant `product_id` if
            it exists instead of finding a variant based on the combination.

            If there is no combination, that means we definitely want a
            variant and not something that will have no_variant set.

        :param add_qty: float with the quantity for which to get the info,
            indeed some pricelist rules might depend on it.

        :param pricelist: `product.pricelist` the pricelist to use
            (can be none, eg. from SO if no partner and no pricelist selected)

        :param parent_combination: if no combination and no product_id are
            given, it will try to find the first possible combination, taking
            into account parent_combination (if set) for the exclusion rules.

        :param only_template: boolean, if set to True, get the info for the
            template only: ignore combination and don't try to find variant

        :return: dict with product/combination info:

            - product_id: the variant id matching the combination (if it exists)

            - product_template_id: the current template id

            - display_name: the name of the combination

            - price: the computed price of the combination, take the catalog
                price if no pricelist is given

            - list_price: the catalog price of the combination, but this is
                not the "real" list_price, it has price_extra included (so
                it's actually more closely related to `lst_price`), and it
                is converted to the pricelist currency (if given)

            - has_discounted_price: True if the pricelist discount policy says
                the price does not include the discount and there is actually a
                discount applied (price < list_price), else False
        """
        self.ensure_one()
        # get the name before the change of context to benefit from prefetch
        display_name = self.display_name

        display_image = True
        quantity = self.env.context.get('quantity', add_qty)
        context = dict(self.env.context, quantity=quantity, pricelist=pricelist.id if pricelist else False)
        product_template = self.with_context(context)

        combination = combination or product_template.env['product.template.attribute.value']

        if not product_id and not combination and not only_template:
            combination = product_template._get_first_possible_combination(parent_combination)

        if only_template:
            product = product_template.env['product.product']
        elif product_id and not combination:
            product = product_template.env['product.product'].browse(product_id)
        else:
            product = product_template._get_variant_for_combination(combination)

        if product:
            # We need to add the price_extra for the attributes that are not
            # in the variant, typically those of type no_variant, but it is
            # possible that a no_variant attribute is still in a variant if
            # the type of the attribute has been changed after creation.
            no_variant_attributes_price_extra = [
                ptav.price_extra for ptav in combination.filtered(
                    lambda ptav:
                    ptav.price_extra and
                    ptav not in product.product_template_attribute_value_ids
                )
            ]
            if no_variant_attributes_price_extra:
                product = product.with_context(
                    no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
                )
            list_price = product.price_compute('list_price')[product.id]
            price = product.price if pricelist else list_price
            display_image = bool(product.image_128)
            display_name = product.display_name
            price_extra = (product.price_extra or 0.0) + (sum(no_variant_attributes_price_extra) or 0.0)
        else:
            current_attributes_price_extra = [v.price_extra or 0.0 for v in combination]
            product_template = product_template.with_context(
                current_attributes_price_extra=current_attributes_price_extra)
            price_extra = sum(current_attributes_price_extra)
            list_price = product_template.price_compute('list_price')[product_template.id]
            price = product_template.price if pricelist else list_price
            display_image = bool(product_template.image_128)

            combination_name = combination._get_combination_name()
            if combination_name:
                display_name = "%s (%s)" % (display_name, combination_name)

        if pricelist and pricelist.currency_id != product_template.currency_id:
            list_price = product_template.currency_id._convert(
                list_price, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
                fields.Date.today()
            )
            price_extra = product_template.currency_id._convert(
                price_extra, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
                fields.Date.today()
            )

        price_without_discount = list_price if pricelist and pricelist.discount_policy == 'without_discount' else price
        has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount,
                                                                                           price) == 1

        return {
            'product_id': product.id,
            'product_template_id': product_template.id,
            'display_name': display_name,
            'display_image': display_image,
            'price': product.lst_price,
            'list_price': product.lst_price,
            'price_extra': product.lst_price,
            'has_discounted_price': has_discounted_price,
        }
