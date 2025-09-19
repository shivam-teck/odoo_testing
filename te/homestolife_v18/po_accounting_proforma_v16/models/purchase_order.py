from odoo import api, fields, models, _
from datetime import date, timedelta
from odoo.tools import format_amount


class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    payments_by_terms = fields.One2many('payments.by.term', 'po_id')
    payment_journal_id = fields.Many2one('account.journal', "Payment Journal")

    @api.onchange('payment_term_id')
    def compute_payments_by_terms(self):
        for order in self:
            order.payments_by_terms = False
            values = []
            if order.payment_term_id:
                payment_terms = order.payment_term_id._compute_terms(
                    date_ref=order.date_order or fields.Date.today(),
                    currency=order.currency_id or order.company_id.currency_id,
                    tax_amount_currency=order.amount_tax,
                    tax_amount=order.amount_tax,
                    untaxed_amount_currency=order.amount_untaxed,
                    untaxed_amount=order.amount_untaxed,
                    company=order.company_id,
                    sign=1
                )
                percent = 0.0
                percent += payment_terms['percent']
                if payment_terms['value'] == 'balance':
                    payment_terms['percent'] = 100 - percent
                values.append((0, 0,
                               {
                                   'name': payment_terms['desc'],
                                   'percent': payment_terms['percent'] or 0.0,
                                   'due_date': payment_terms['date'],
                                   'value': payment_terms['company_amount'],
                                   'order_id': order.id
                               }))

            order.payments_by_terms = values


class POPaymentsByTerms(models.Model):
    _inherit = 'po.payments.term'
    _order = "sequence,id"

    name = fields.Char("Description")
    sequence = fields.Integer(default=10)
    po_id = fields.Many2one('purchase.order')
    value = fields.Float("Amount")
    percent = fields.Float("Amount in %")
    due_date = fields.Date("Due Date")
    # is_payment_received = fields.Boolean("Payment Received ?")
    payment_recv_date = fields.Date("Payment Received Date")
    amount_received = fields.Float("Amount Received")
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', 'Currency', related='company_id.currency_id', readonly=True,
                                  required=True)

    def open_create_payment_wizard(self):
        payment_method_lines = self.po_id.payment_journal_id._get_available_payment_method_lines('inbound')
        res_id = self.env['payment.wiz'].sudo().create({
            'term_id': self.id,
            'order_id': self.po_id.id,
            'journal_id': self.po_id.payment_journal_id.id,
            'payment_method_id': payment_method_lines[0]._origin.id or False,
            'amount': self.value - self.amount_received,
            'payment_date': date.today(),
            'memo': "Advance Payment for" + str(self.po_id.name)
        })
        return {
            'name': _('Register Payment'),
            'res_model': 'payment.wiz',
            'view_mode': 'form',
            'target': 'new',
            'res_id': res_id.id,
            'type': 'ir.actions.act_window',
        }

    def view_payments(self):
        payments = self.env['account.payment'].sudo().search([('term_id', '=', self.id)])
        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('term_id', '=', self.id)],
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id
            })
        return action
