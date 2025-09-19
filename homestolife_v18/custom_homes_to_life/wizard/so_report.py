from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SoReport(models.TransientModel):
    _name = 'so.report'

    lead_id = fields.Many2one('crm.lead', string='Lead', readonly=True)
    expected_revenue = fields.Float(string='Expected Revenue', readonly=True)
    lead_created_by = fields.Many2one('res.users', string='Created By', readonly=True)
    lead_create_date = fields.Datetime(string='Create Date', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    so_customer = fields.Many2one('res.partner', string='Customer', readonly=True)
    so_stage = fields.Selection(
        selection=[
            ('draft', "Quotation"),
            ('sent', "Quotation Sent"),
            ('sale', "Sales Order"),
            ('done', "LReportocked"),
            ('cancel', "Cancelled"),
        ],
        string="So Status",
        readonly=True
        )
    so_price = fields.Float(string='Total Price', readonly=True)

    def get_data(self):
        self.env.cr.execute(f'delete from so_report;')
        query = """insert into so_report (lead_id,expected_revenue,lead_created_by,lead_create_date,sale_order_id,so_customer,so_stage,so_price)
        select lead.id, lead.expected_revenue, lead.user_id, lead.create_date, order_id.id, order_id.partner_id, order_id.state, order_id.amount_total from crm_lead as lead
        full join sale_order order_id on lead.id = order_id.opportunity_id """
        self.env.cr.execute(query)

        return {
            'name': _('Report'),
            'res_model': 'so.report',
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
        }
