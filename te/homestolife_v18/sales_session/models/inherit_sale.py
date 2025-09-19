from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    session_id = fields.Many2one('session.session', readonly=True)

    @api.model
    def create(self, vals):
        session = self.env['session.session'].search(
            [('opened_by', '=', vals['user_id']), ('active_session', '=', True)])
        vals['session_id'] = session.id
        if not self.delivery_status:
            self.delivery_status = 'draft'
            print(self.delivery_status)
        if not vals['session_id']:
            raise ValidationError('Please Activate Session')

        res = super(SaleOrderInherit, self).create(vals)
        return res
