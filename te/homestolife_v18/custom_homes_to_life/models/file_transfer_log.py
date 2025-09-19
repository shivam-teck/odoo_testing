from odoo import api, fields, models


class FileTransferLog(models.Model):
    _name = "file.transfer.log"

    sale_order = fields.Char(string="Sale Order")
    status = fields.Selection([('success', 'Success'),
                               ('exception', 'Exception'),
                               ], string="Status")

    log_exception = fields.Text(string="Log Exception")
    ftp_host = fields.Many2one("ftp.configuration")

    export_time = fields.Datetime('Export Time')
    so_id = fields.Many2one('sale.order', 'Sale Order')
    file_name = fields.Char('File Name')

    # company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company.id)



