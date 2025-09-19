from odoo import models, fields


class UTMSource(models.Model):
    _inherit = 'utm.source'

    medium_id = fields.Many2one('utm.medium', string="Medium", required=True, help="The medium this source belongs to.")
