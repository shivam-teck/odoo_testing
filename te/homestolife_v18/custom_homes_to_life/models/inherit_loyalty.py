from odoo import models, api, fields, _


class InheritLoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    exclude_tax = fields.Boolean(default=False)
