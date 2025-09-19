from odoo import api, fields, models, _
from datetime import date, timedelta
from odoo.tools import format_amount
from odoo.exceptions import UserError, ValidationError


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    payments_by_terms = fields.One2many('account.payment', 'order_id')
    total_additional_discount = fields.Float(string='Total Additional Discount')
    payment_journal_id = fields.Many2one('account.journal', "Payment Journal")
    create_invoice = fields.Boolean('Create Invoice', default=False, compute='compute_create_invoice', store=True)
    balance_amount = fields.Float('Pending Amount', compute='compute_balance_amount', store=True)
    hide_confirm_button = fields.Boolean('Hide Confirm', default=False)
    send_to_ftp = fields.Boolean('File Sent to FTP', default=False, readonly=True)

    @api.depends('payments_by_terms.amount_company_currency_signed', 'payments_by_terms', 'state', 'amount_total')
    def compute_balance_amount(self):
        for rec in self:
            if rec.company_id.id != 2:
                value = sum(rec.payments_by_terms.filtered(
                    lambda l: l.state in ['paid']).mapped('amount_company_currency_signed')) or 0
                rec.balance_amount = rec.amount_total - value
                total_25 = rec.amount_total * (25 / 100)
                if int(total_25) <= int(value) and rec.state in ['draft', 'sent']:
                    rec.hide_confirm_button = True
                else:
                    rec.hide_confirm_button = False
            else:
                rec.hide_confirm_button = True

    def payment_create(self):
        # action = self.env.ref('po_accounting_proforma_v16.action_create_payment_wizard').read()[0]
        # return action
        payment_method_lines = self.id
        res_id = self.env['create.payment'].sudo().create({
            'order_id': self.id,
            'payment_date': date.today(),
            'amount': self.balance_amount,
            'memo': "Payment for " + str(self.name)
        })
        return {
            'name': _('Register Payment'),
            'res_model': 'create.payment',
            'view_mode': 'form',
            'target': 'new',
            'res_id': res_id.id,
            'type': 'ir.actions.act_window',
        }

    @api.depends('state', 'balance_amount')
    def compute_create_invoice(self):
        for rec in self:
            if rec.state in ['sale', 'done']:
                # rec.create_invoice = True
                # total_amount_received = sum(rec.payments_by_terms.mapped('amount_received'))
                # if rec.balance_amount <= 0.0:
                rec.create_invoice = True
            else:
                rec.create_invoice = False

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
                                   # 'percent': term['percent'] or 0.0,
                                   # 'due_date': term['date'],
                                   # 'value': term['company_amount'],
                                   'order_id': order.id
                               }))

            order.payments_by_terms = values

# def action_quotation_send(self):
#     res = super(SaleOrderInherit, self).action_quotation_send()
#     message_to_write = ''' '''
#     ctx = res['context']
#     for term in self.payments_by_terms.filtered(lambda l: not l.is_payment_received).sorted(key='due_date', reverse=True):
#         message_to_write += term.name + ''' Due on '''+ term.due_date +''' : '''+ format_amount(self.env, term.value, term.currency_id) +'''\n'''
#
#     for term in self.payments_by_terms.filtered(lambda l: not l.is_payment_received).sorted(key='due_date', reverse=True):
#         message_to_write += term.name + ''' Due on '''+ term.due_date +''' : '''+ format_amount(self.env, term.value, term.currency_id) +'''\n'''
#
#     ctx['payment_msg'] = message_to_write
#     res['context'] = ctx
#     return res


class PaymentsByTerms(models.Model):
    _name = 'payments.by.term'
    _order = "sequence,id"

    name = fields.Char("Description")
    sequence = fields.Integer(default=10)
    order_id = fields.Many2one('sale.order')
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

    # @api.onchange('amount_received')
    # def update_payment_received(self):
    #     for line in self:
    #         if line.amount_received > 0:
    #             line.payment_recv_date = date.today()

    def open_create_payment_wizard(self):
        payment_method_lines = self.order_id.payment_journal_id._get_available_payment_method_lines('inbound')
        res_id = self.env['payment.wiz'].sudo().create({
            'term_id': self.id,
            'order_id': self.order_id.id,
            'journal_id': self.order_id.payment_journal_id.id,
            'payment_method_id': payment_method_lines[0]._origin.id or False,
            'amount': self.value - self.amount_received,
            'payment_date': date.today(),
            'memo': "Advance Payment for" + str(self.order_id.name)
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
            'view_mode': 'list,form',
            'domain': [('term_id', '=', self.id)],
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id
            })
        return action
