from odoo import models, api, fields, _
import ftplib
import pandas as pd
import pytz
import datetime
import numpy as np
import datetime as DT


class FtpStock(models.Model):
    _name = 'sap.stock'
    _rec_name = 'material_code'

    plant = fields.Char(string='Plant')
    storage_location = fields.Char(string='Storage Location')
    material_code = fields.Char(string='Material Code')
    batch_no = fields.Char(string='Batch No')
    configuration = fields.Char(string='Configuration')
    front_article = fields.Char(string='Front Article')
    back_article = fields.Char(string='Back Article')
    quantity = fields.Char(string='Quantity')
    sap_table = fields.Char(string="SAP Table")
    remarks = fields.Char(string="Remarks")
    last_sink_time = fields.Datetime(string="Last Synch Time", readonly=True)

    def fetch_details(self):
        active_ftp = self.env['ftp.configuration'].search([('active_ftp', '=', True)])
        if active_ftp:
            filename = False

            try:
                ftp = ftplib.FTP(active_ftp.hostname, active_ftp.username, active_ftp.password)
                ftp.encoding = "utf-8"
                ftp.cwd("/PRD/INPOS/STOCK")
                file_names = ftp.nlst()
                if len(file_names)>0:
                    for name in file_names:
                        filename = name
                        ftp.retrbinary('RETR ' + filename, open(filename, 'wb').write)
                        new_path = '/PRD/INPOS/ARCHIVED_OUT/' + filename
                        ftp.rename(filename, new_path)
                        ftp.quit()
                        df = pd.read_csv(filename)
                        df = df.fillna('')
                        data = df.to_dict('index')
                        b = []
                        for rec in data.values():
                            data = {}
                            for i, j in rec.items():
                                if j is not False:
                                    data[i] = j
                            b.append(data)
                        c = []
                        records = self.env['sap.stock'].search([])
                        records.unlink()
                        current_time = fields.Datetime.now()
                        # print(b,'b')
                        for rec in b:
                            plant = rec.get('Plant', False)
                            storage_location = rec.get('Storage Loc.', False)
                            material_code = rec.get('Material code', False)
                            batch_no = rec.get('Batch', False)
                            configuration = rec.get('Configuration', False)
                            front_article = rec.get('Front Article', False)
                            back_article = rec.get('Back Article', False)
                            quantity = rec.get('Quantity', False)
                            sap_table = rec.get('SAP table', False)
                            remarks = rec.get('Remarks', False)
                            tz = pytz.timezone('Asia/Kolkata')  # Set the timezone to IST
                            last_sink = pytz.UTC.localize(current_time).astimezone(tz)

                            inventory_values = {
                                'plant': plant,
                                'storage_location': storage_location,
                                'material_code': material_code,
                                'batch_no': batch_no,
                                'configuration': configuration,
                                'front_article': front_article,
                                'back_article': back_article,
                                'quantity': quantity,
                                'sap_table': sap_table,
                                'remarks': remarks,
                                'last_sink_time': datetime.datetime.now()
                            }
                            self.env['sap.stock'].create(inventory_values)
                        transfer_log = [(0, 0, {
                            'sale_order': filename,
                            'status': 'success',
                            'log_exception': f"File Fetched successfully",
                            'ftp_host': active_ftp.id,
                            'export_time': DT.datetime.now(),
                            'file_name': name,

                        })]
                        active_ftp.write({'file_transfer_ids': transfer_log})
                else:
                    ftp.quit()

            except Exception as e:
                transfer_log = [(0, 0, {
                    'sale_order': filename,
                    'status': 'exception',
                    'log_exception': f"Fetching Failed due to {e}",
                    'ftp_host': active_ftp.id,
                    'export_time': DT.datetime.now()

                })]
                active_ftp.write({'file_transfer_ids': transfer_log})

