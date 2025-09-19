from odoo import models, api, fields, _


class SessionConfig(models.Model):
    _name = 'session.config'

    name = fields.Char('Session Name')
    active_session = fields.Boolean('Active Session', default=False)

    def start_session(self):
        self.active_session = True

    def end_session(self):
        self.active_session = False
