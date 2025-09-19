from odoo import models, api, fields, _
from pytz import timezone
from datetime import datetime
import pandas as pd
import pysftp
from pathlib import Path
import os
import ftplib
from odoo.exceptions import UserError, ValidationError


import datetime as DT


class InheritAccountPayments(models.Model):
    _inherit = 'account.payment'

    payment_date = fields.Datetime()
    payment_date_confirm = fields.Datetime(store=True)
    send_to_ftp = fields.Boolean(default=False, readonly=True)
    hide_send_to_ftp = fields.Boolean(default=False, compute='compute_hide_send_to_ftp')

    @api.depends('company_id')
    def compute_hide_send_to_ftp(self):
        for rec in self:
            if rec.company_id.business_type == 'fofo':
                rec.hide_send_to_ftp = True
            else:
                rec.hide_send_to_ftp = False



    def action_post(self):
        ''' draft -> posted '''
        # Do not allow posting if the account is required but not trusted
        for payment in self:
            if payment.require_partner_bank_account and not payment.partner_bank_id.allow_out_payment:
                raise UserError(_(
                    "To record payments with %(method_name)s, the recipient bank account must be manually validated. "
                    "You should go on the partner bank account of %(partner)s in order to validate it.",
                    method_name=self.payment_method_line_id.name,
                    partner=payment.partner_id.display_name,
                ))
        self.filtered(lambda pay: pay.outstanding_account_id.account_type == 'asset_cash').state = 'paid'
        # Avoid going back one state when clicking on the confirm action in the payment list view and having paid expenses selected
        # We need to set values to each payment to avoid recomputation later
        self.filtered(lambda pay: pay.state in {False, 'draft', 'in_process'}).state = 'paid'

        # payment_date_confirm = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
        # self.payment_date_confirm = payment_date_confirm
        # if self.company_id.business_type != 'fofo':
        #     tuple(map(self.create_data, self))
        # else:
        #     pass

    #     hold ftp transfer

    # def send_customer_via_ftp(self, file_name, df):
    #     active_ftp = self.env['ftp.configuration'].search([('active_ftp', '=', True)])
    #     port = int(active_ftp.port)
    #     try:
    #         ftp = ftplib.FTP(active_ftp.hostname, active_ftp.username, active_ftp.password)
    #         ftp.encoding = "utf-8"
    #         ftp.cwd("/PRD/INPOS/APAYMENT")
    #         # ftp.cwd("/home/po/Saleorder")
    #         company = self.env.company
    #         payment_id = self.env['account.payment'].search([('name', '=', file_name)])
    #         payment_date = payment_id.payment_date_confirm
    #         payment_date = str(payment_date.year) + str(payment_date.month) + str(payment_date.day)
    #         file_n = False
    #         if company.business_type == 'coco':
    #             file_n = f'POS_AP_COCO_{payment_id.order_id.name}_{payment_date}.csv'
    #         elif company.business_type == 'ho':
    #             file_n = f'POS_AP_HO_{payment_id.order_id.name}_{payment_date}.csv'
    #         elif company.business_type == 'fofo':
    #             file_n = f'POS_AP_FOFO_{payment_id.order_id.name}_{payment_date}.csv'
    #         dir_path = Path(f'payments/')
    #         # dir_path = Path(f'/home/odoo/shivam/odoo18_set)
    #         with open(os.path.join(dir_path, file_n), 'w') as fp:
    #             df.to_csv(fp, encoding='utf-8', index=False)
    #         if payment_id.send_to_ftp == False and payment_id.state in ['paid']:
    #             with open(os.path.join(dir_path, file_n), 'rb') as filee:
    #                 ftp.storbinary(f"STOR {file_n}", filee, 262144)
    #                 # print('File removed')
    #                 os.remove(f'{dir_path}/{file_n}')
    #                 filee.close()
    #                 ftp.dir()
    #                 ftp.quit()
    #                 ftp.close()
    #
    #             if payment_id:
    #                 payment_id.send_to_ftp = True
    #
    #                 print("Connection successfully established ... ")
    #                 transfer_log = [(0, 0, {
    #                     'sale_order': file_name,
    #                     'status': 'success',
    #                     'log_exception': 'File Transfer Successfully',
    #                     'ftp_host': active_ftp.id,
    #                     'export_time': DT.datetime.now(),
    #                     'file_name': file_n
    #
    #                 })]
    #                 active_ftp.write({'file_transfer_ids': transfer_log})
    #
    #     except Exception as e:
    #         transfer_log = [(0, 0, {
    #             'sale_order': file_name,
    #             'status': 'exception',
    #             'log_exception': f"Transfer Failed due to {e}",
    #             'ftp_host': active_ftp.id,
    #             'export_time': DT.datetime.now()
    #         })]
    #         active_ftp.write({'file_transfer_ids': transfer_log})
    #         search_todo = self.env['mail.activity.type'].sudo().search([('name', '=', 'To Do')])
    #         search_admin = self.env['res.users'].sudo().search([('name', '=', 'Administrator')])
    #         search_model = self.env['ir.model'].sudo().search([('model', '=', 'account.payment')])
    #         today = DT.date.today()
    #         week_ago = today + DT.timedelta(days=7)
    #         todays_date = today.strftime("%Y-%m-%d")
    #         self.env['mail.activity'].create({
    #             'activity_type_id': search_todo.id,
    #             'summary': 'Failed to transfer file to ftp',
    #             'date_deadline': week_ago,
    #             'user_id': search_admin.id,
    #             'res_model_id': search_model.id,
    #             'res_id': self.id
    #         })

    def create_data(self, payment_id):
        line = lambda rec: {
            'Sales Document': payment_id.order_id.name or '',
            'No of items': len(payment_id.order_id.order_line.filtered(lambda x: not x.display_type)) or '',
            'Sale Office': '',
            'Booking Date': payment_id.payment_date_confirm.date() or '',
            'Payment Method': payment_id.payment_method_line_id.name or '',
            'Amount Paid in Local Currency': payment_id.amount or '',
            'Payment Document Number': payment_id.name or '',
            'Remark': payment_id.memo or '',
            'Document No': '',
            'Created By': payment_id.order_id.name or '',
            'Time': payment_id.payment_date_confirm.time()

        }
        data_list = [line(rec) for rec in payment_id]

        df = pd.DataFrame(data_list, index=[0])

        self.send_customer_via_ftp(payment_id.name, df)

    def send_payment(self):
        if self.company_id.business_type != 'fofo':
            tuple(map(self.create_data, self))
        else:
            pass

