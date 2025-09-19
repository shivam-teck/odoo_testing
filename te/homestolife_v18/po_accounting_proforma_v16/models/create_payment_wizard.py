from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CreatePayment(models.TransientModel):
    _name = 'create.payment'

    journal_id = fields.Many2one('account.journal', string="Payment Type")
    payment_method_id = fields.Many2one('account.payment.method.line', string="Payment Method",
                                        domain="[('id', 'in', available_payment_method_line_ids)]")
    amount = fields.Float("Amount")
    payment_date = fields.Date("Payment Date", default=fields.Date.context_today)
    memo = fields.Char("Narration")
    order_id = fields.Many2one('sale.order', string="Order")

    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True, tracking=True)

    # @api.model
    # def default_get(self, fields):
    #     res = super(CreatePayment, self).default_get(fields)
    #     if 'journal_id' in fields:
    #         res['journal_id'] = self.order_id.id

    @api.depends('payment_type', 'journal_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines(pay.payment_type)
            to_exclude = pay._get_payment_method_codes_to_exclude()
            if to_exclude:
                pay.available_payment_method_line_ids = pay.available_payment_method_line_ids.filtered(lambda x: x.code not in to_exclude)

    def _get_payment_method_codes_to_exclude(self):
        # can be overriden to exclude payment methods based on the payment characteristics
        self.ensure_one()
        return []


    def create_payment_so(self):
        cost = 0.0
        if self.order_id:
            if round(self.amount,2) > self.order_id.amount_total:
                raise UserError(_("Payment cannot be more than Order Amount."))
            if self.order_id.balance_amount == 0.0 and round(self.amount,2) > self.order_id.balance_amount:
                raise UserError(_("Payment cannot be more than Order Amount."))

        # if self.amount > self.order_id.balance_amount:
        #     raise UserError(_("Payment amount is greater than Balance amount !!"))

        payment = self.env['account.payment'].create({
            'partner_id': self.order_id.partner_id.id,
            'payment_type': 'inbound',
            'amount': self.amount,
            'date': self.payment_date,
            'memo': "Payment for " + str(self.order_id.name),
            'journal_id': self.journal_id.id,
            'payment_method_line_id': self.payment_method_id.id,
            'currency_id': self.order_id.currency_id.id,
            'order_id': self.order_id.id,
        })

        # self.term_id.amount_received += payment.amount
        # self.term_id.payment_recv_date = self.payment_date
        # payment.action_post()

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': payment.id,
        }
        create_payment_list = []
        # create_payments_by_term = (0, 0, {
        #     'name': self.memo,
        #     'value': self.amount,
        #     'payment_recv_date': self.payment_date,
        #     'amount_received': self.amount,
        # })
        # create_payment_list.append(create_payments_by_term)
        # self.order_id.write({'payments_by_terms':create_payment_list})
        return action
