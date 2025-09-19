from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError

class FtpConfiguration(models.Model):
    _name = 'ftp.configuration'
    _rec_name = 'hostname'

    hostname = fields.Char(string="Host Name", required=True)
    username = fields.Char(string="User Name", required=True)
    password = fields.Char(string="Password", required=True)
    port = fields.Char(string="Port")
    active_ftp = fields.Boolean(string="Active", default=False)
    file_transfer_ids = fields.One2many("file.transfer.log", "ftp_host",
                                        string="File Transfer Log")

    def only_one_active_ftp(self, vals):
        is_active = self.search([('active_ftp', '=', True)])
        if vals.get('active') and is_active:
            raise ValidationError('There can only be one active Ftp Server')

    @api.model
    def create(self, vals):
        self.only_one_active_ftp(vals)
        res = super(FtpConfiguration, self).create(vals)
        return res

    def write(self, vals):
        self.only_one_active_ftp(vals)
        res = super(FtpConfiguration, self).write(vals)
        return res

