from odoo import models, api, fields, _
import datetime
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class Sessions(models.Model):
    _name = 'session.session'
    _rec_name = 'session_no'

    # name = fields.Char('Session')
    session_no = fields.Char(string='Ref', copy=False, readonly=True, default=lambda self: _('New'))
    active_session = fields.Boolean('Active Session', readonly=True)
    opened_by = fields.Many2one('res.users', string='Opened By', default=lambda self: self.env.user)
    opening_date = fields.Datetime(string='Opening Date', readonly=1)
    closing_date = fields.Datetime(string='Closing Date', readonly=1)
    starting_balance = fields.Float(string='Starting Balance')
    ending_balance = fields.Float(string='Ending Balance')
    sale_order_ids = fields.One2many('sale.order', 'session_id', string='Sale Order', readonly=True)
    is_activated = fields.Boolean(default=False)
    so_confirm_count = fields.Integer(compute='compute_so_confirm_count')
    so_count = fields.Integer(compute='compute_so_count')
    payment_count = fields.Integer(compute='compute_payment_count')

    @api.model
    def create(self, vals):
        if vals.get('session_no', _('New')) == _('New'):
            vals['session_no'] = self.env['ir.sequence'].next_by_code('session.session') or _('New')
            vals['active_session'] = True
            vals['opening_date'] = datetime.today().strftime('%Y-%m-%d')
            vals['is_activated'] = True
            self.only_one_active_session(vals)
        res = super(Sessions, self).create(vals)
        return res

    def write(self, vals):
        res = super(Sessions, self).write(vals)
        return res

    def only_one_active_session(self, vals):
        is_active = self.search([('active_session', '=', True), ('opened_by', '=', vals['opened_by'])])
        if is_active:
            raise ValidationError('There can only be one active Session')
        else:
            pass

    def start_session(self):
        self.active_session = True
        self.is_activated = True

    def end_session(self):
        self.closing_date = datetime.today().strftime('%Y-%m-%d')
        self.active_session = False

    def get_confirm_so(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree',
            'res_model': 'sale.order',
            'domain': [('session_id', '=', self.id), ('state', '=', 'sale')],
            'context': "{'create': False}"
        }

    def compute_so_confirm_count(self):
        for record in self:
            record.so_confirm_count = self.env['sale.order'].search_count(
                [('session_id', '=', self.id), ('state', '=', 'sale')])


    def get_so(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotation',
            'view_mode': 'tree',
            'res_model': 'sale.order',
            'domain': [('session_id', '=', self.id), ('state', 'in', ['draft', 'sent'])],
            'context': {'create': False}
        }

    def compute_so_count(self):
        for record in self:
            record.so_count = self.env['sale.order'].search_count(
                [('session_id', '=', self.id), ('state', 'in', ['draft', 'sent'])])

    def get_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Account Payment',
            'view_mode': 'tree',
            'res_model': 'account.payment',
            'domain': [('session_id', '=', self.id), ('state', 'in', ['posted'])],
            'context': {'create': False}
        }

    def compute_payment_count(self):
        for record in self:
            record.payment_count = self.env['account.payment'].search_count(
                [('session_id', '=', self.id), ('state', 'in', ['posted'])])






