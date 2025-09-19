from odoo import models, api, fields, _
import logging

class InheritCrmLead(models.Model):
    _inherit = "crm.lead"

    memo = fields.Text('Memo')
    sale_staff = fields.Many2one('hr.employee')
    is_ho_account = fields.Boolean('HO account', default=False, compute='compute_ho_account')
    campaign_name = fields.Char(string="Campaign Name")
    ad_name = fields.Char(string="Ad Name")
    ad_set_name = fields.Char(string="Ad Set Name")
    budget = fields.Char(string="What is your budget?")
    buy_time = fields.Char(string="How Soon You Want to Buy?")
    meta_lead_id = fields.Char(string="Meta Lead ID")
    platform = fields.Char(string="Platform")
    product_interested = fields.Char(string="Product Interested")
    call_status = fields.Selection([
        ('1st_call', '1st Call Done'),
        ('2nd_call', '2nd Call Done'),
        ('3rd_call', '3rd Call Done'),
    ], string="Call Status", tracking=True)

    @api.depends('company_id', 'partner_id')
    def compute_ho_account(self):
        for rec in self:
            rec.is_ho_account = rec.company_id.business_type == 'ho'

    @api.model
    def create(self, vals):

        if 'ad_set_name' in vals and vals['ad_set_name']:
            mapping = self.env['company.mapping'].search([('ad_set_name', '=', vals['ad_set_name'])], limit=1)
            if mapping:
                vals['company_id'] = mapping.company_id.id
                vals['user_id'] = mapping.salesperson_id.id if mapping.salesperson_id else False

        vals.setdefault('team_id', self.env['crm.team'].search([], limit=1).id)

        return super(InheritCrmLead, self).create(vals)

    def write(self, vals):

        if 'ad_set_name' in vals and vals['ad_set_name']:
            mapping = self.env['company.mapping'].search([('ad_set_name', '=', vals['ad_set_name'])], limit=1)
            if mapping:
                vals['company_id'] = mapping.company_id.id
                vals['user_id'] = mapping.salesperson_id.id if mapping.salesperson_id else False

        return super(InheritCrmLead, self).write(vals)
