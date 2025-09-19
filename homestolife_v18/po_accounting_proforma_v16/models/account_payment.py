from odoo import api, fields, models,_
from datetime import date, timedelta
from odoo.tools import format_amount
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    order_id = fields.Many2one('sale.order', string="Order")
    term_id = fields.Many2one('payments.by.term')
    sap_customer_code = fields.Char(string="SAP Customer Code", compute="_compute_sap_customer_code")

    @api.ondelete(at_uninstall=False)
    def restrict_delete(self):
        if self.state == 'posted':
            raise ValidationError("You can delete payment one's the payment is done.")

    @api.depends('order_id.partner_id')
    def _compute_sap_customer_code(self):
        """
        Fetch the SAP customer code from the related partner of the order.
        """
        for payment in self:
            payment.sap_customer_code = payment.order_id.partner_id.sap_customer_code