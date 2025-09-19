from odoo import models, api, fields, _


class FranchiseMargin(models.Model):
    _name = 'franchise.margin'
    _rec_name = 'product_category'

    product_category = fields.Many2one('product.category')
    margin_rate = fields.Float(string='Margin%')
    company = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    res_company1 = fields.Many2one('res.company')



class FranchiseProductCategory(models.Model):
    _name = 'franchise.product.category'
    _rec_name = 'product_category'

    product_category = fields.Char(string="Product Category", required=True)
