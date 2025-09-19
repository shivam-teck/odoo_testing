from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError, AccessError
import pandas as pd
import pysftp
import datetime as DT
import ftplib
import base64
from pathlib import Path
import os
from odoo.fields import Command
from collections import defaultdict
import random

from itertools import groupby


def _generate_random_reward_code():
    return str(random.getrandbits(32))


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_untaxed = fields.Monetary(string="Untaxed Amount", store=True, compute='_compute_amounts', tracking=5)

    amount_total = fields.Monetary(string="Grand Total", store=True, compute='_compute_amounts', tracking=4)
    total_amount_received = fields.Float(string='Total Amount Received', compute='compute_amount_received')
    total_additional_discount = fields.Float(string='Total Additional Discount', compute='compute_total_discount')
    is_change_so = fields.Boolean('Is Change SO', default=False)
    so_change_date = fields.Datetime(string='So Change Date')
    origin = fields.Char(
        string="Source Document",
        help="Reference of the document that generated this sales order request", compute='compute_origin')
    sale_staff = fields.Many2one('hr.employee', compute='compute_sale_staff', store=True)
    hide_ftp_button = fields.Boolean(default=False, compute='compute_hide_ftp_button')
    send_to_ftp = fields.Boolean('File Sent to FTP', default=False, readonly=True)
    is_ho_account = fields.Boolean('HO account', default=False)
    company_type = fields.Selection(related='company_id.business_type')
    ftp_log_ids = fields.One2many("file.transfer.log", "so_id",
                                  string="File Transfer Log")
    oc_no = fields.Char('OC Number', store=True)
    display_so_name = fields.Char(
        string="Source Document",
        help="Reference of the document that generated this sales order request",
        compute='compute_display_so_name', store=True
    )

    @api.depends('origin', 'company_id', 'partner_id', 'client_order_ref')
    def compute_display_so_name(self):
        for rec in self:
            if rec.company_id.business_type == 'ho':
                search_purchase_order = self.env['purchase.order'].sudo().search([('name', '=', rec.client_order_ref)],
                                                                                 limit=1)
                if search_purchase_order:
                    for po in search_purchase_order:
                        if po.company_id.name == rec.partner_id.name:
                            customer_name = self.env['sale.order'].sudo().search([('name', '=', po.origin)], limit=1)
                            partner_name = customer_name.partner_id.name or ''
                            rec.display_so_name = f"{rec.origin} {partner_name}" if rec.origin else partner_name
                            break
                else:
                    rec.display_so_name = False
            else:
                rec.display_so_name = False

    @api.depends('company_id')
    def compute_hide_ftp_button(self):
        for rec in self:
            if rec.company_id.business_type == 'fofo':
                rec.hide_ftp_button = True
            else:
                rec.hide_ftp_button = False

    @api.depends('opportunity_id')
    def compute_sale_staff(self):
        for rec in self:
            if rec.opportunity_id:
                rec.sale_staff = rec.opportunity_id.sale_staff if rec.opportunity_id.sale_staff else False
            else:
                rec.sale_staff = False

    # connect to ftp
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    @api.depends('company_id')
    def compute_origin(self):
        for rec in self:
            if rec.company_id.business_type == 'ho':
                rec.is_ho_account = True
                search_purchase_order = self.env['purchase.order'].sudo().search([('name', '=', rec.client_order_ref)])
                if search_purchase_order:
                    for po in search_purchase_order:
                        if po.company_id.name == rec.partner_id.name:
                            rec.origin = po.origin
                            rec.oc_no = po.oc_no
                            break
                        else:
                            rec.origin = False
                else:
                    rec.origin = False
            else:
                rec.origin = False

    def send_via_ftp(self, file_name, df, df_case_good, order_id):
        active_ftp = self.env['ftp.configuration'].search([('active_ftp', '=', True)])
        port = int(active_ftp.port)
        try:
            ftp = ftplib.FTP(active_ftp.hostname, active_ftp.username, active_ftp.password)
            ftp.encoding = "utf-8"
            ftp.cwd("/PRD/INPOS/PO")
            company = self.env.company
            sale_order = self.env['sale.order'].search([('name', '=', file_name)])
            so_date = sale_order.date_order
            so_date = str(so_date.year) + str(so_date.month) + str(so_date.day)
            # dict(self._fields['stage'].selection).get(self.stage)
            if df_case_good.empty:
                print('DataFrame is empty!')

                file_n = False
                if company.business_type == 'coco':
                    file_n = f'POS_COCO_{file_name}_{so_date}.csv'
                elif company.business_type == 'ho':
                    file_n = f'POS_HO_{file_name}_{so_date}.csv'
                elif company.business_type == 'fofo':
                    file_n = f'FOFO_HO_{file_name}_{so_date}.csv'
                # dir_path = Path(f'/home/po/Saleorder/')
                dir_path = Path(f'saleorder/')
                with open(os.path.join(dir_path, file_n), 'w') as fp:
                    df.index += 1
                    df.index.name = 'so_number_item'
                    if df.index.name is not None:
                        df.reset_index(inplace=True)

                    # Define the desired position for the index column (e.g., as the first column)
                    desired_index_position = 0

                    # Reorder the columns to place the index column at the desired position
                    columns = df.columns.tolist()
                    index_column = columns.pop(desired_index_position)
                    columns.insert(3, index_column)
                    df = df.reindex(columns=columns)
                    df.to_csv(fp, encoding='utf-8', index=False)
                    print(df)
                if sale_order.send_to_ftp == False and sale_order.state in ['sale', 'done']:
                    with open(os.path.join(dir_path, file_n), 'rb') as filee:
                        ftp.storbinary(f"STOR {file_n}", filee, 262144)
                        self.attach_file(file_name, df, df_case_good, order_id, file_n)
                        os.remove(f'{dir_path}/{file_n}')
                        # print('File removed')
                        filee.close()
                        ftp.dir()
                        ftp.quit()
                        ftp.close()
                    if sale_order:
                        sale_order.send_to_ftp = True

                        print("Connection successfully established ... ")
                        transfer_log = [(0, 0, {
                            'sale_order': file_name,
                            'so_id': order_id.id,
                            'status': 'success',
                            'log_exception': 'File Transfer Successfully',
                            'ftp_host': active_ftp.id,
                            'export_time': DT.datetime.now(),
                            'file_name': file_n

                        })]
                        active_ftp.write({'file_transfer_ids': transfer_log})
                        self.message_post(body="File Transfer Success")

            else:
                counter = 0
                list_df = [df, df_case_good]
                for rec in list_df:
                    if counter == 0:
                        counter += 1
                        if rec.empty:
                            pass
                        elif not rec.empty:
                            # write condition for only cg
                            file_n = False
                            if company.business_type == 'coco':
                                file_n = f'POS_COCO_{file_name}_{so_date}.csv'
                            elif company.business_type == 'ho':
                                file_n = f'POS_HO_{file_name}_{so_date}.csv'
                            elif company.business_type == 'fofo':
                                file_n = f'FOFO_HO_{file_name}_{so_date}.csv'
                            # dir_path = Path(f'/home/po/Saleorder/')
                            dir_path = Path(f'saleorder/')
                            with open(os.path.join(dir_path, file_n), 'w') as fp:
                                rec.index += 1
                                rec.index.name = 'so_number_item'
                                if rec.index.name is not None:
                                    rec.reset_index(inplace=True)

                                # Define the desired position for the index column (e.g., as the first column)
                                desired_index_position = 0

                                # Reorder the columns to place the index column at the desired position
                                columns = rec.columns.tolist()
                                index_column = columns.pop(desired_index_position)
                                columns.insert(3, index_column)
                                df = rec.reindex(columns=columns)
                                df.to_csv(fp, encoding='utf-8', index=False)

                            if sale_order.state in ['sale', 'done']:
                                with open(os.path.join(dir_path, file_n), 'rb') as filee:
                                    ftp.storbinary(f"STOR {file_n}", filee, 262144)
                                    self.attach_file(file_name, df, df_case_good, order_id, file_n)
                                    os.remove(f'{dir_path}/{file_n}')
                                    filee.close()
                                    if sale_order:
                                        print("Connection successfully established ... ")
                                        transfer_log = [(0, 0, {
                                            'sale_order': file_name,
                                            'so_id': order_id.id,
                                            'status': 'success',
                                            'log_exception': 'File Transfer Successfully',
                                            'ftp_host': active_ftp.id,
                                            'export_time': DT.datetime.now(),
                                            'file_name': file_n

                                        })]
                                        active_ftp.write({'file_transfer_ids': transfer_log})
                                        self.message_post(body="File Transfer Success")

                    elif counter == 1:
                        file_n = False
                        if company.business_type == 'coco':
                            file_n = f'POS_COCO_{file_name}_{so_date}CaseGood.csv'
                        elif company.business_type == 'ho':
                            file_n = f'POS_HO_{file_name}_{so_date}CaseGood.csv'
                        elif company.business_type == 'fofo':
                            file_n = f'FOFO_HO_{file_name}_{so_date}CaseGood.csv'
                        # dir_path = Path(f'/home/po/Saleorder/')
                        dir_path = Path(f'saleorder/')
                        with open(os.path.join(dir_path, file_n), 'w') as fp:
                            rec.index += 1
                            rec.index.name = 'so_number_item'
                            if rec.index.name is not None:
                                rec.reset_index(inplace=True)

                            # Define the desired position for the index column (e.g., as the first column)
                            desired_index_position = 0

                            # Reorder the columns to place the index column at the desired position
                            columns = rec.columns.tolist()
                            index_column = columns.pop(desired_index_position)
                            columns.insert(3, index_column)
                            df = rec.reindex(columns=columns)
                            df.to_csv(fp, encoding='utf-8', index=False)
                            # counter += 1
                        if sale_order.state in ['sale', 'done']:
                            with open(os.path.join(dir_path, file_n), 'rb') as filees:
                                ftp.storbinary(f"STOR {file_n}", filees, 262144)
                                self.attach_file(file_name, df, df_case_good, order_id, file_n)
                                os.remove(f'{dir_path}/{file_n}')
                                filees.close()
                                print('yes')
                                if sale_order:
                                    sale_order.send_to_ftp = True
                                    print("Connection successfully established ... ")
                                    transfer_log = [(0, 0, {
                                        'sale_order': file_name,
                                        'so_id': order_id.id,
                                        'status': 'success',
                                        'log_exception': 'File Transfer Successfully',
                                        'ftp_host': active_ftp.id,
                                        'export_time': DT.datetime.now(),
                                        'file_name': file_n

                                    })]
                                    self.message_post(body="File Transfer Success")

                                    active_ftp.write({'file_transfer_ids': transfer_log})

                ftp.dir()
                ftp.quit()
                ftp.close()

        except Exception as e:
            transfer_log = [(0, 0, {
                'sale_order': file_name,
                'so_id': order_id.id,
                'status': 'exception',
                'log_exception': f"Transfer Failed due to {e}",
                'ftp_host': active_ftp.id,
                'export_time': DT.datetime.now()

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
                'res_id': self.id,
            })

    def attach_file(self, file_name, df, df_case_good, order_id, file_n):
        # path = "/home/po/Saleorder/"
        path = "saleorder/"
        dir_list = os.listdir(path)
        attachment_list = []
        for rec in dir_list:
            if rec == file_n:

                search_attachments = self.env['ir.attachment'].search([('name', '=', file_name)])
                if not search_attachments:
                    file = open(
                        # f"/home/po/Saleorder/{rec}", "rb")
                        f"saleorder/{rec}", "rb")

                    create_attachment = {
                        'type': 'binary',
                        'datas': base64.standard_b64encode(file.read()),
                        'res_id': order_id.id,
                        'res_model': 'sale.order',
                        'res_name': order_id.name,
                        'name': rec,
                        'display_name': rec,
                    }
                    attachment_list.append((create_attachment))

                self.env['ir.attachment'].create(attachment_list)

    @staticmethod
    def get_config(rec):
        config = rec.product_id.product_template_attribute_value_ids.filtered(
            lambda x: 'Config' in x.attribute_id.mapped('name'))
        return config and config.display_name.replace('Config:', '') or ''

    @staticmethod
    def get_article(rec):
        article = rec.product_id.product_template_attribute_value_ids.filtered(
            lambda x: 'Article Type' in x.attribute_id.mapped('name'))
        return article and article.display_name.replace('Article Type:', '') or ''

    def create_data(self, order_id):
        no_of_line_items = 0
        if order_id.origin:
            search_origin_partner = self.env['sale.order'].sudo().search([('name', '=', order_id.origin)])
        else:
            search_origin_partner = False

        line = lambda rec: {'site code': order_id.company_id.site_code,
                            'Business Type(COCO/FOFO/HO)': self.compute_bussiness_type(order_id),
                            'Sales Type': rec.route_id.name if rec.order_id.company_id.business_type == 'coco' else rec.route if rec.route else '',
                            'customer_sold_to': order_id.partner_id.sap_customer_code if order_id.partner_id.sap_customer_code else '',
                            'customer_skip_to': order_id.partner_shipping_id.sap_customer_code if order_id.partner_shipping_id.sap_customer_code else '',
                            'so_number': order_id.name,
                            'po_date': order_id.date_order.date(),
                            'ETD': order_id.commitment_date.date() if order_id.commitment_date else '',
                            'ETA': order_id.expected_date.date() if order_id.expected_date else '',
                            # 'Reference': order_id.partner_id.name or '',
                            'Reference': f"{order_id.origin}/{order_id.client_order_ref}/{search_origin_partner.partner_id.name}" \
                                if order_id.origin and order_id.client_order_ref and search_origin_partner.partner_id.name \
                                else order_id.partner_id.name or '',
                            'Model': rec.product_id.name if rec.product_id.is_case_good == False else rec.product_id.default_code,
                            'config': self.get_config(rec),
                            'article_type': self.get_article(rec),
                            'article_type_1': rec.article1.material if rec.article1.material else '',
                            'article_type_2': rec.articletype_2.material if rec.articletype_2.material else '',
                            'QTY': rec.product_uom_qty,
                            'U/P(INR)': rec.price_unit,
                            'Item Discount': round(rec.discount, 2), 'Amt(INR)': rec.price_subtotal,
                            'Header Surcharge': '',
                            'Item Surcharge': '',
                            'Special Remark': search_origin_partner.partner_id.name if search_origin_partner else ''}
        # Print the Reference value for debugging
        # for rec in order_id.order_line:
        #     reference_value = f"{order_id.origin}/{order_id.client_order_ref}/{search_origin_partner.partner_id.name}" \
        #         if order_id.origin and order_id.client_order_ref and search_origin_partner.partner_id.name \
        #         else order_id.partner_id.name or ''
        #     print(f"Reference Value: {reference_value}")

        data_list = [line(rec) for rec in
                     order_id.order_line.filtered(lambda
                                                      x: not x.display_type and x.product_template_id.type != 'service' and x.product_template_id.is_case_good == False)]
        print(data_list, 'without case good')

        case_good = [line(rec) for rec in
                     order_id.order_line.filtered(lambda
                                                      x: not x.display_type and x.product_template_id.type != 'service' and x.product_template_id.is_case_good == True)]
        print(case_good, 'with case good')
        df = pd.DataFrame(data_list)
        df_case_good = pd.DataFrame(case_good)
        self.send_via_ftp(order_id.name, df, df_case_good, order_id)

    def write(self, values):
        if values.get("state") == 'sale' and not self.commitment_date and self.company_id.id != 2:
            raise ValidationError('Delivery Date is Required')
        if self.state == "draft" or self.state == "sent":
            if values.get("state") == "sale":
                if self.order_line and self.company_id.business_type != 'ho':
                    for rec in self.order_line:
                        if not rec.route_id and rec.product_id.type != 'service':
                            raise ValidationError('Select Routes')
        result = super(InheritSaleOrder, self).write(values)
        return result

    def compute_bussiness_type(self, order_id):
        if order_id.origin:
            search_origin_so = self.env['sale.order'].sudo().search([('name', '=', order_id.origin)])
            if search_origin_so:
                company_type = "FOFO" if search_origin_so.company_id.business_type == 'fofo' else "COCO"
            else:
                company_type = 'COCO' if order_id.company_id.business_type == 'coco' else 'FOFO' if order_id.company_id.business_type == 'fofo' else 'HO'
        else:
            company_type = 'COCO' if order_id.company_id.business_type == 'coco' else 'FOFO' if order_id.company_id.business_type == 'fofo' else 'HO'
        return company_type

    # def compute_sale_type(self,order_id):
    #     if order_id.origin:
    #

    def send_so(self):
        if self.company_id.business_type != 'fofo':
            self.send_to_ftp = False
            if not self.partner_id.sap_customer_code:
                raise ValidationError('SAP Customer Code Required in Customer')
            elif not self.partner_shipping_id.sap_customer_code or self.partner_shipping_id.sap_customer_code == '1':
                raise ValidationError('SAP Customer Code Required in Delivery Address')
            tuple(map(self.create_data, self))
            tuple(map(self.compute_bussiness_type, self))
        else:
            pass
        #     hold ftp transfer

        # tuple(map(self.create_data, self))

    # def send_so(self):
    #     tuple(map(self.create_data, self))
    #     confirm func here

    def _prepare_confirmation_values(self):
        """ Prepare the sales order confirmation values.

        Note: self can contain multiple records.

        :return: Sales Order confirmation values
        :rtype: dict
        """
        return {
            'state': 'sale',
            'date_order': self.so_change_date
        }

    def action_confirm(self):
        if self.company_id.business_type == "coco":
            if not self.partner_id.sap_customer_code:
                raise UserError("SAP Customer Code is required before confirming the Sale Order.")

        if self.is_change_so == False:
            self.so_change_date = fields.Datetime.now()
            self.date_order = self.so_change_date
            self.is_change_so = True
        """ Confirm the given quotation(s) and set their confirmation date.

        If the corresponding setting is enabled, also locks the Sale Order.

        :return: True
        :rtype: bool
        :raise: UserError if trying to confirm locked or cancelled SO's
        """
        for order in self:
            error_msg = order._confirmation_error_message()
            if error_msg:
                raise UserError(error_msg)

        self.order_line._validate_analytic_distribution()

        for order in self:
            if order.partner_id in order.message_partner_ids:
                continue
            order.message_subscribe([order.partner_id.id])

        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        user = self[:1].create_uid
        if user and user.sudo().has_group('sale.group_auto_done_setting'):
            # Public user can confirm SO, so we check the group on any record creator.
            self.action_lock()

        if self.env.context.get('send_email'):
            self._send_order_confirmation_mail()

        if self.company_id.business_type == 'coco':
            email_template = self.env.ref('custom_homes_to_life.mail_template_sale_confirmation_so')

            additional_recipients = "pravin.patil@homestolife.in,oc.confirmation@homestolife.in"

            if email_template:
                for order in self:
                    email_template.with_context(
                        email_to=order.partner_id.email or '',
                        email_cc=additional_recipients,
                        auto_delete=False
                    ).send_mail(order.id, force_send=True)

        return True

    @api.depends('order_line.additional_discount')
    def compute_total_discount(self):
        for rec in self:
            rec.total_additional_discount = sum(rec.order_line.mapped('additional_discount')) or 0

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        res = super()._convert_to_tax_base_line_dict()
        res['additional_discount'] = self.additional_discount
        # res['product_location_type'] = self.product_location_type
        return res

    @api.depends('payments_by_terms.amount_company_currency_signed', 'state')
    def compute_amount_received(self):
        for rec in self:
            value = sum(rec.payments_by_terms.filtered(
                lambda l: l.state == 'paid').mapped('amount_company_currency_signed')) or 0
            rec.total_amount_received = value

    #     for exc discount
    def _discountable_order(self, reward):
        """
        Returns the discountable and discountable_per_tax for a discount that applies to the whole order
        """
        self.ensure_one()
        assert reward.discount_applicability == 'order'

        discountable = 0
        discountable_per_tax = defaultdict(int)
        lines = self.order_line if reward.program_id.is_payment_program else (
                self.order_line - self._get_no_effect_on_threshold_lines())
        for line in lines:
            if line.tax_id:
                # Ignore lines from this reward
                if not line.product_uom_qty or not line.price_unit:
                    continue
                line_discountable = line.price_unit * line.product_uom_qty * (1 - (line.discount or 0.0) / 100.0)
                discountable += line.price_total
                discountable_per_tax[line.tax_id] += line_discountable
        return discountable, discountable_per_tax

    def _get_reward_values_discount(self, reward, coupon, **kwargs):
        self.ensure_one()
        assert reward.reward_type == 'discount'

        # Figure out which lines are concerned by the discount
        # cheapest_line = self.env['sale.order.line']
        discountable = 0

        discountable_per_tax = defaultdict(int)
        reward_applies_on = reward.discount_applicability
        sequence = max(self.order_line.filtered(lambda x: not x.is_reward_line).mapped('sequence'), default=10) + 1
        if reward_applies_on == 'order':
            discountable, discountable_per_tax = self._discountable_order(reward)
        elif reward_applies_on == 'specific':
            discountable, discountable_per_tax = self._discountable_specific(reward)
        elif reward_applies_on == 'cheapest':
            discountable, discountable_per_tax = self._discountable_cheapest(reward)
        # Discountable should never surpass the order's current total amount
        discountable = min(self.amount_total, discountable)
        if not discountable:
            if not reward.program_id.is_payment_program and any(
                    line.reward_id.program_id.is_payment_program for line in self.order_line):
                return [{
                    'name': _("TEMPORARY DISCOUNT LINE"),
                    'product_id': reward.discount_line_product_id.id,
                    'price_unit': 0,
                    'product_uom_qty': 0,
                    'product_uom': reward.discount_line_product_id.uom_id.id,
                    'reward_id': reward.id,
                    'coupon_id': coupon.id,
                    'points_cost': 0,
                    'reward_identifier_code': _generate_random_reward_code(),
                    'sequence': sequence,
                    'tax_id': [(Command.CLEAR, 0, 0)]
                }]
            raise UserError(_('There is nothing to discount'))
        max_discount = reward.currency_id._convert(reward.discount_max_amount, self.currency_id, self.company_id,
                                                   fields.Date.today()) or float('inf')
        if reward.discount_mode == 'per_point':
            max_discount = min(max_discount,
                               reward.currency_id._convert(reward.discount * self._get_real_points_for_coupon(coupon),
                                                           self.currency_id, self.company_id, fields.Date.today()))
        elif reward.discount_mode == 'per_order':
            max_discount = min(max_discount,
                               reward.currency_id._convert(reward.discount, self.currency_id, self.company_id,
                                                           fields.Date.today()))
        elif reward.discount_mode == 'percent':
            max_discount = min(max_discount, discountable * (reward.discount / 100))
        # Discount per taxes
        reward_code = _generate_random_reward_code()
        point_cost = reward.required_points if not reward.clear_wallet else self._get_real_points_for_coupon(coupon)
        if reward.discount_mode == 'per_point' and not reward.clear_wallet:
            # Calculate the actual point cost if the cost is per point
            converted_discount = self.currency_id._convert(min(max_discount, discountable), reward.currency_id,
                                                           self.company_id, fields.Date.today())
            point_cost = converted_discount / reward.discount
        # Gift cards and eWallets are considered gift cards and should not have any taxes
        if reward.program_id.is_payment_program:
            return [{
                'name': reward.description,
                'product_id': reward.discount_line_product_id.id,
                'price_unit': -min(max_discount, discountable),
                'product_uom_qty': 1.0,
                'product_uom': reward.discount_line_product_id.uom_id.id,
                'reward_id': reward.id,
                'coupon_id': coupon.id,
                'points_cost': point_cost,
                'reward_identifier_code': reward_code,
                'sequence': sequence,
                'tax_id': [(Command.CLEAR, 0, 0)],
            }]
        discount_factor = min(1, (max_discount / discountable)) if discountable else 1
        if reward.program_id.is_payment_program == True:
            mapped_taxes = False
        else:
            mapped_taxes = {tax: self.fiscal_position_id.map_tax(tax) for tax in discountable_per_tax}
        reward_dict = {tax: {
            'name': _(
                'Discount: %(desc)s%(tax_str)s',
                desc=reward.description,
                tax_str=len(discountable_per_tax) and any(t.name for t in mapped_taxes[tax]) and _(
                    ' - On product with the following taxes: %(taxes)s',
                    taxes=", ".join(mapped_taxes[tax].mapped('name'))) or '',
            ),
            'product_id': reward.discount_line_product_id.id,
            'price_unit': -(
                    price * discount_factor) if reward.program_id.exclude_tax == False else reward.discount_line_product_id.lst_price,
            'product_uom_qty': 1.0,
            'product_uom': reward.discount_line_product_id.uom_id.id,
            'reward_id': reward.id,
            'coupon_id': coupon.id,
            'points_cost': 0,
            'reward_identifier_code': reward_code,
            'sequence': sequence,
            'tax_id': [(Command.CLEAR, 0, 0)] + [(Command.LINK, tax.id, False) for tax in
                                                 mapped_taxes[tax]] if reward.program_id.exclude_tax == False else False
        } for tax, price in discountable_per_tax.items() if price}
        # We only assign the point cost to one line to avoid counting the cost multiple times
        if reward_dict:
            reward_dict[next(iter(reward_dict))]['points_cost'] = point_cost
        # Returning .values() directly does not return a subscribable list
        return list(reward_dict.values())

    def total_re_amount(self):
        print('ok')

class InheritProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_default_pricelist = fields.Boolean('Default Pricelist', default=False)

    @api.model
    def create(self, vals):
        self.only_one_default_pricelist(vals)
        res = super(InheritProductPricelist, self).create(vals)
        return res

    def write(self, vals):
        self.only_one_default_pricelist(vals)
        res = super(InheritProductPricelist, self).write(vals)
        return res

    def only_one_default_pricelist(self, vals):
        is_active = self.search([('is_default_pricelist', '=', True)])
        if vals.get('is_default_pricelist') and is_active:
            raise ValidationError('There can only be one default Pricelist')
