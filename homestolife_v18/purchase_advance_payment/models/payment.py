from odoo import fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    purchase_id = fields.Many2one(
        "purchase.order",
        "Purchase Order",
        readonly=True,
    )
    payment_reference = fields.Char(string="Payment ID", store=True)

    def _validate_and_confirm_related_orders(self, payment):
        if not payment.payment_reference:
            raise UserError("Payment Reference is missing. Cannot proceed.")

        related_payments = self.env['account.payment'].sudo().search([
            ('id', '=', payment.payment_reference),
            ('state', '!=', 'posted'),
        ])

        if not related_payments:
            raise UserError(f"No Unposted related payments found for Payment Reference: {payment.payment_reference}")

        if related_payments:
            related_payments.sudo().filtered(lambda p: p.state != 'posted').action_post()
