from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
from datetime import date, datetime, timedelta
from datetime import datetime


class ImportProduct(models.Model):
    _name = 'import.product'

    upload_product_file = fields.Binary('File')

    def convert_to_df(self):
        csv_data = self.upload_product_file
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_product(self):
        df = self.convert_to_df()
        data = df.to_dict('index')
        b = []  # b is list of dictionary with data of each row
        for rec in data.values():
            data = {}
            for i, j in rec.items():
                if j is not False:
                    data[i] = j
            b.append(data)
        c = []  # c is list of column names with data  of each row
        list = []
        line_items = []
        list_attributes = []
        for rec in b:
            product_name = rec.get('Model', False)
            config = rec.get('Config', False)
            product_id = self.env['product.template'].search([('name', '=', product_name)])
            search_vendor_tax = self.env['account.tax'].search(
                [('name', '=', 'GST 18%'), ('type_tax_use', '=', 'purchase')])
            search_customer_tax = self.env['account.tax'].search(
                [('name', '=', 'GST 18%'), ('type_tax_use', '=', 'sale')])
            # vendor purchase tax
            if not product_id:
                keys_list = [key for key, val in rec.items() if val]
                c.append(keys_list)
                list = c[-1]
                line_items = []
                list_attributes = []
                if not config:
                    product_details = {
                        'name': product_name,
                        'sale_ok': True,
                        'last_update': date.today(),
                        'purchase_ok': True,
                        'detailed_type': 'product',
                        'expense_policy': 'no',
                        'supplier_taxes_id': search_vendor_tax,
                        'taxes_id': search_customer_tax
                    }
                    product_id = self.env['product.template'].create(product_details)

                    list_attributes = []
                    search_attribute_config = self.env['product.attribute'].search([('name', '=', 'Article Type')])
                    for value in search_attribute_config.value_ids:

                        for k in list:
                            if k.strip().lower() == value.name.strip().lower():
                                list_attributes.append(value.id)
                    product_attributes = (0, 0, {
                        'attribute_id': search_attribute_config.id,
                        'value_ids': [item for item in list_attributes]

                    })
                    line_items.append(product_attributes)

                    product_id.write({'attribute_line_ids': line_items})
                    line_items = []
                    list = []
            else:
                list_line_item = []
                if config:
                    search_attribute_value = self.env['product.attribute.value'].search([('name', '=', config)])
                    if product_id.attribute_line_ids:
                        for rec in product_id.attribute_line_ids:
                            list_line_item.append(rec.display_name)
                            if rec.display_name == 'Config':
                                search_attribute_config = self.env['product.attribute'].search(
                                    [('name', '=', 'Config')])
                                if not search_attribute_value:
                                    list_of_unavailable_conf = []
                                    conf_data = (0, 0, {
                                        'name': config
                                    })
                                    list_of_unavailable_conf.append(conf_data)
                                    search_attribute_config.write({'value_ids': list_of_unavailable_conf})
                                search_attribute_value = self.env['product.attribute.value'].search(
                                    [('name', '=', config)])
                                rec.value_ids = [(4, search_attribute_value.id)]
                                product_id.write({'last_update': date.today()})

                            else:
                                if 'Config' not in list_line_item:
                                    search_attribute_config = self.env['product.attribute'].search(
                                        [('name', '=', 'Config')])

                                    search_attribute_value = self.env['product.attribute.value'].search(
                                        [('name', '=', config)])
                                    if not search_attribute_value:
                                        list_of_unavailable_conf = []
                                        conf_data = (0, 0, {
                                            'name': config
                                        })
                                        list_of_unavailable_conf.append(conf_data)
                                        search_attribute_config.write({'value_ids': list_of_unavailable_conf})
                                    search_attribute_value = self.env['product.attribute.value'].search(
                                        [('name', '=', config)])
                                    product_attributes = (0, 0, {
                                        'attribute_id': search_attribute_config.id,
                                        'value_ids': search_attribute_value

                                    })
                                    line_items.append(product_attributes)
                                    product_id.write({'last_update': date.today()})
                                    product_id.write({'attribute_line_ids': line_items})

                else:
                    for rec in product_id.attribute_line_ids:
                        list_attributes = []
                        update_attribute = []
                        search_attribute_config = self.env['product.attribute'].search(
                            [('name', '=', 'Article Type')])
                        for value in search_attribute_config.value_ids:
                            list_attributes.append(value.id)
                        if rec.display_name == 'Article Type':
                            for values in rec.value_ids:
                                update_attribute.append(values.id)
                            for val in list_attributes:
                                if val not in update_attribute:
                                    rec.value_ids = [(4, val)]





