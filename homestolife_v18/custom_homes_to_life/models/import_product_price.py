from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
import datetime
from datetime import date, datetime, timedelta


class ImportProductPrice(models.Model):
    _name = 'import.product.price'

    upload_product_price_file = fields.Binary('File')

    def convert_to_df(self):
        csv_data = self.upload_product_price_file
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_product_price(self):
        df = self.convert_to_df()
        df.columns = ["Model", "Config", "BLT", "BLJ", "SKA", "HON", "QUE", "BMO", "BVP", "ANP", "NCP", "TOP",
                      "VOP/BRP", "NPP", "NNP", "SKP/PEP", "BVS", "ANS", "NCS", "TOS", "VOS/BRS", "BV", "AN/NW", "NC",
                      "TO",
                      "VO/BR", "NP/OH", "NN", "SK/PE", "BV+FAB", "AN+FAB", "NC+FAB"]
        # df = df.loc[[df['Config'].notnull()]]
        data = df.to_dict('index')
        data = data.values()
        column_names = df.columns[2:]
        for rec in data:
            product_name = rec.get('Model', False)
            config = rec.get('Config', False)
            if config is False:
                continue
            product_id = self.env['product.product'].search([('name', '=', product_name)])
            # print([ref   for ref in product_id.product_template_variant_value_ids])
            # print(product_id.product_template_attribute_value_ids.mapped('name'))
            product_id = product_id.filtered(
                lambda x: config.strip() in x.product_template_attribute_value_ids.mapped('name'))
            if product_id:
                for col_name in column_names:
                    product_variant = product_id.filtered(
                        lambda x: col_name.strip() in x.product_template_attribute_value_ids.mapped('name'))
                    # for attr in product_id.product_template_variant_value_ids:
                    #     if attr.name == col_name.strip():
                    price = rec.get(col_name.strip(), 0)
                    if price:
                        try:
                            value = int(price.strip().replace(',', ''))
                            product_variant.lst_price = float(value)
                            product_variant.last_update = date.today()
                        except:
                            value = int(float(price))
                            product_variant.lst_price = float(value)
                            product_variant.last_update = date.today()

