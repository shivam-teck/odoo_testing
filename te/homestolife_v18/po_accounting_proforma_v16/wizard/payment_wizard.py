from odoo import api, fields, models,_
from odoo.exceptions import UserError

class PaymentWiz(models.TransientModel):
    _name = "payment.wiz"

    journal_id = fields.Many2one('account.journal',string="Journal")
    payment_method_id = fields.Many2one('account.payment.method.line',string="Payment Method")
    amount = fields.Float("Amount")
    payment_date = fields.Date("Payment Date",default=fields.Date.context_today)
    memo = fields.Char("Memo")
    order_id = fields.Many2one('sale.order',string="Order")
    term_id = fields.Many2one('payments.by.term')

    def create_payment(self):
        if self.amount > self.term_id.value - self.term_id.amount_received:
            raise UserError(_("Payment amount is greater than partial term amount !!"))

        payment = self.env['account.payment'].create({
            'partner_id':self.order_id.partner_id.id,
            'payment_type':'inbound',
            'amount':self.amount,
            'date':self.payment_date,
            'ref':self.memo,
            'journal_id':self.journal_id.id,
            'payment_method_line_id':self.payment_method_id.id,
            'currency_id':self.order_id.currency_id.id,
            'order_id':self.order_id.id,
            'term_id':self.term_id.id
        })

        self.term_id.amount_received += payment.amount
        self.term_id.payment_recv_date = self.payment_date
        payment.action_post()

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': payment.id,
        }
        return action