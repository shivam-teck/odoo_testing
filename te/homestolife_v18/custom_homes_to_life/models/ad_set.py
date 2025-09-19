from odoo import models, fields

class CompanyMapping(models.Model):
    _name = 'company.mapping'
    _description = 'Mapping between Ad Set Name and Company'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ad_set_name'

    ad_set_name = fields.Char(string="Ad Set Name", required=True, unique=True, tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, tracking=True)
    salesperson_id = fields.Many2one('res.users', string="Salesperson", required=True, tracking=True)
