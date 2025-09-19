from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError


class InheritAccountPayments(models.Model):
    _inherit = 'account.payment'

    session_id = fields.Many2one('session.session', 'Session')

    @api.model
    def create(self, vals):
        session = self.env['session.session'].search([('opened_by', '=', self.env.user.id),
                                                      ('active_session', '=', True)])
        vals['session_id'] = session.id
        if not vals['session_id']:
            raise ValidationError('Please Activate Session')

        res = super(InheritAccountPayments, self).create(vals)
        return res

    def write(self, vals):
        session = self.env['session.session'].search([('opened_by', '=', self.env.user.id),
                                                      ('active_session', '=', True)])

        vals['session_id'] = session.id
        if not vals['session_id']:
            raise ValidationError('Please Activate Session')
        res = super(InheritAccountPayments, self).write(vals)
        return res
