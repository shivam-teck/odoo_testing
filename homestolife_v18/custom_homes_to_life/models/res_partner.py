from odoo import models, api, fields, _
import pandas as pd
import pysftp
from pathlib import Path
import os
from odoo.exceptions import UserError, ValidationError
from datetime import date
import datetime as DT


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char(string='Customer Code', copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self._default_company())
    # company_id = fields.Many2one('res.company', string='Company')
    sap_customer_code = fields.Char(string='SAP Customer Code')


    def _default_company(self):
        company = self.env.company.id
        return company

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.search([('phone', operator, name)] + args, limit=limit)
        if not recs.ids:
            return super(InheritResPartner, self).name_search(name=name, args=args,operator=operator,limit=limit)
        return [(rec.id, rec.display_name) for rec in recs]


    _sql_constraints = [
        ('phone_uniq', 'UNIQUE (phone)', 'You can not have two users with the same phone number !')]

    @api.model
    def create(self, vals):
        if vals.get('customer_code', _('New')) == _('New'):
            vals['customer_code'] = self.env['ir.sequence'].next_by_code('res.partner') or _('New')
        res = super(InheritResPartner, self).create(vals)
        return res

    def send_customer_via_ftp(self, file_name, df):
        active_ftp = self.env['ftp.configuration'].search([('active_ftp', '=', True)])
        port = int(active_ftp.port)
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        try:
            with pysftp.Connection(host=active_ftp.hostname, username=active_ftp.username, password=active_ftp.password,
                                   port=port,
                                   cnopts=cnopts) as sftp:
                file = f'{file_name}.csv'
                print(file_name)
                dir_path = Path('/home/po/Customer/')

                with open(os.path.join(dir_path, file), 'w') as fp:
                    df.index += 1
                    # df.index.name = 'so_number_item'
                    df.to_csv(fp, encoding='utf-8', index=True)

                localFilePath = f'/home/po/Customer/{file}'
                remoteFilePath = f'/www/homestolife_888/Customer/{file}'
                search_customer = self.env['res.partner'].search([('name', '=', file_name)])
                # if search_customer.send_to_ftp == False:
                sftp.put(localFilePath, remoteFilePath)
                # os.remove(localFilePath)
                # if search_customer:
                #     search_customer.send_to_ftp = True
                print("Connection successfully established ... ")
                transfer_log = [(0, 0, {
                    'sale_order': file_name,
                    'status': 'success',
                    'log_exception': 'File Transfer Successfully',
                    'ftp_host': active_ftp.id,

                })]
                active_ftp.write({'file_transfer_ids': transfer_log})
        except Exception as e:
            transfer_log = [(0, 0, {
                'sale_order': file_name,
                'status': 'exception',
                'log_exception': f"Transfer Failed due to {e}",
                'ftp_host': active_ftp.id,

            })]
            active_ftp.write({'file_transfer_ids': transfer_log})
            search_todo = self.env['mail.activity.type'].sudo().search([('name', '=', 'To Do')])
            search_admin = self.env['res.users'].sudo().search([('name', '=', 'Administrator')])
            search_model = self.env['ir.model'].sudo().search([('model', '=', 'sale.order')])
            today = DT.date.today()
            week_ago = today + DT.timedelta(days=7)
            todays_date = today.strftime("%Y-%m-%d")
            self.env['mail.activity'].create({
                'activity_type_id': search_todo.id,
                'summary': 'Failed to transfer file to ftp',
                'date_deadline': week_ago,
                'user_id': search_admin.id,
                'res_model_id': search_model.id,
                'res_id': self.id
            })

    def create_data(self, partner_id):
        type_gst = dict(partner_id._fields['l10n_in_gst_treatment'].selection).get(partner_id.l10n_in_gst_treatment)
        print(type_gst)
        line = lambda rec: {
            'customer code': partner_id.customer_code or '',
            'customer name': partner_id.name,
            'email': partner_id.email or '',
            'phone': partner_id.phone or '',
            'street1': partner_id.street or '',
            'street2': partner_id.street2 or '',
            'city': partner_id.city or '',
            'state': partner_id.state_id.name or '',
            'country': partner_id.country_id.name or '',
            'zipcode': partner_id.zip or '',
            'gst_type': type_gst or '',
            'gst number': partner_id.vat or ''

        }
        print(line)
        data_list = [line(rec) for rec in partner_id]

        df = pd.DataFrame(data_list, index=[0])
        print(df)

        self.send_customer_via_ftp(partner_id.name, df)

    def send_customer(self):
        tuple(map(self.create_data, self))


class InheritResCompany(models.Model):
    _inherit = 'res.company'

    sap_customer_code = fields.Char(string='SAP Customer Code')
    site_code = fields.Char(string='Site Code')
    business_type = fields.Selection([('ho', 'HO'), ('coco', 'COCO'), ('fofo', 'FOFO')])
    margin = fields.Float(string='Margin(%)')
    margin_ids = fields.One2many("franchise.margin", "res_company1", string="Margin")
    apply_vendor_pricelist = fields.Boolean('Apply Vendor Pricelist')
