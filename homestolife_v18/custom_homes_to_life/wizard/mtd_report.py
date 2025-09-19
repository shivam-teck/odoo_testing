from odoo import api, fields, models, _
from datetime import datetime, timedelta


class MtdReport(models.TransientModel):
    _name = 'mtd.report'

    # Date Fields
    todays_date = fields.Datetime(string='Date', default=datetime.today())
    first_date_year = fields.Datetime(compute='compute_year_date')
    start_date = fields.Datetime(compute='compute_first_date')
    last_date = fields.Datetime(compute='compute_last_date')

    # Lead Fields
    today_lead = fields.Integer(compute='compute_today_lead')
    mtd_lead = fields.Integer(compute='compute_mtd_lead')
    ytd_lead = fields.Integer(compute='compute_ytd_lead')

    # Walking Fields
    day_walking = fields.Integer(compute='compute_day_walking')
    mtd_walking = fields.Integer(compute='compute_mtd_walking')
    ytd_walking = fields.Integer(compute='compute_ytd_walking')

    # Opportunity Fields
    opp_created = fields.Integer(compute='compute_opp_created')
    mtd_opp_created = fields.Integer(compute='compute_mtd_opp_created')
    ytd_opp_created = fields.Integer(compute='compute_ytd_opp_created')

    value_new_opp = fields.Float(compute='compute_value_new_opp')
    mtd_value_opportunity = fields.Float(compute='compute_mtd_value_opp')
    ytd_value_opportunity = fields.Float(compute='compute_ytd_value_opp')
    active_opportunity = fields.Integer(compute='compute_active_opportunity')

    # Revenue Payments Fields
    day_revenue = fields.Integer(compute='compute_day_revenue')
    mtd_revenue = fields.Integer(compute='compute_mtd_revenue')
    ytd_revenue = fields.Integer(compute='compute_ytd_revenue')

    # Invoice Fields
    day_invoice = fields.Integer(compute='compute_day_invoice')
    mtd_invoice = fields.Integer(compute='compute_mtd_invoice')

    # Quotation sent
    day_quotation_count = fields.Integer(compute='compute_day_quotation_count')
    mtd_quotation_count = fields.Integer(compute='compute_mtd_quotation_count')
    ytd_quotation_count = fields.Integer(compute='compute_ytd_quotation_count')

    # Quotation Value
    day_quotation_value = fields.Integer(compute='compute_day_quotation_value')
    mtd_quotation_value = fields.Integer(compute='compute_mtd_quotation_value')
    ytd_quotation_value = fields.Integer(compute='compute_ytd_quotation_value')

    # Revenue Payments Fields
    day_invoice_amount = fields.Integer(compute='compute_day_invoice_amount')
    mtd_invoice_amount = fields.Integer(compute='compute_mtd_invoice_amount')
    ytd_invoice_amount = fields.Integer(compute='compute_ytd_invoice_amount')

    # Google Rating Fields
    day_rating = fields.Integer(compute='compute_day_google_rating')
    mtd_rating = fields.Integer(compute='compute_mtd_google_rating')
    ytd_rating = fields.Integer(compute='compute_ytd_google_rating')

    # Instagram Fields
    day_follower = fields.Integer(compute='compute_day_follower')
    mtd_follower = fields.Integer(compute='compute_mtd_follower')
    ytd_follower = fields.Integer(compute='compute_ytd_follower')

    # Date Functions
    @api.depends('todays_date')
    def compute_first_date(self):
        self.start_date = self.todays_date.replace(day=1)

    @api.depends('todays_date')
    def compute_year_date(self):
        self.first_date_year = self.todays_date.replace(month=1, day=1)

    @api.depends('todays_date')
    def compute_last_date(self):
        next_month = self.todays_date.replace(day=28) + timedelta(days=4)
        self.last_date = next_month - timedelta(days=next_month.day)

    # Lead Function
    @api.depends('todays_date')
    def compute_today_lead(self):
        lead_create = self.env['crm.lead'].search(
            [('type', '=', 'lead'), ('create_date', '>=', self.todays_date.date())])
        self.today_lead = len(lead_create)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_lead(self):
        lead_create = self.env['crm.lead'].search(
            [('type', '=', 'lead'), ('create_date', '<=', self.todays_date.date()),
             ('create_date', '>=', self.start_date.date())])
        self.mtd_lead = len(lead_create)

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_lead(self):
        lead_create = self.env['crm.lead'].search(
            [('type', '=', 'lead'), ('create_date', '<=', self.todays_date.date()),
             ('create_date', '>=', self.first_date_year)])
        self.ytd_lead = len(lead_create)

    # Opportunity Functions
    @api.depends('todays_date', 'start_date')
    def compute_opp_created(self):
        search_opp = self.env['crm.lead'].search(
            [('date_conversion', '>=', self.todays_date.date()),
             ('type', '=', 'opportunity')])
        self.opp_created = len(search_opp)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_opp_created(self):
        search_opp = self.env['crm.lead'].search(
            [('date_conversion', '>=', self.start_date.date()), ('date_conversion', '<=', self.todays_date.date()),
             ('type', '=', 'opportunity')])
        self.mtd_opp_created = len(search_opp)

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_opp_created(self):
        search_opp = self.env['crm.lead'].search(
            [('date_conversion', '>=', self.first_date_year), ('date_conversion', '<=', self.todays_date.date()),
             ('type', '=', 'opportunity')])
        self.ytd_opp_created = len(search_opp)

    @api.depends('todays_date', 'start_date', 'last_date')
    def compute_active_opportunity(self):
        search_active_opp = self.env['crm.lead'].search(
            [('probability', '<', 100), ('type', '=', 'opportunity')])
        self.active_opportunity = len(search_active_opp)

    # opp value
    @api.depends('todays_date')
    def compute_value_new_opp(self):
        search_mtd_new_value_opp = self.env['crm.lead'].search([('type', '=', 'opportunity')])
        current_date_value = search_mtd_new_value_opp.filtered(
            lambda x: x.date_conversion.date() == self.todays_date.date() if x.date_conversion else '').mapped(
            'expected_revenue')
        self.value_new_opp = sum(current_date_value)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_value_opp(self):
        search_mtd_value_opp = self.env['crm.lead'].search(
            [('date_conversion', '>=', self.start_date.date()), ('date_conversion', '<=', self.todays_date),
             ('type', '=', 'opportunity')]).mapped('expected_revenue')
        self.mtd_value_opportunity = sum(search_mtd_value_opp)

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_value_opp(self):
        search_ytd_value_opp = self.env['crm.lead'].search(
            [('date_conversion', '>=', self.first_date_year), ('date_conversion', '<=', self.todays_date),
             ('type', '=', 'opportunity')]).mapped('expected_revenue')
        self.ytd_value_opportunity = sum(search_ytd_value_opp)

    # Invoice Functions
    @api.depends('todays_date')
    def compute_day_invoice(self):
        search_created_invoice = self.env['account.move'].search([])
        invoice_count = search_created_invoice.filtered(
            lambda x: x.invoice_date == self.todays_date.date() if x.invoice_date else '')
        self.day_invoice = len(invoice_count)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_invoice(self):
        search_mtd_created_invoice = self.env['account.move'].search([])
        invoice_mtd_count = search_mtd_created_invoice.filtered(
            lambda
                x: x.invoice_date >= self.start_date.date() and x.invoice_date <= self.todays_date.date() if x.invoice_date else '')
        self.mtd_invoice = len(invoice_mtd_count)

    # Revenue Functions
    @api.depends('todays_date')
    def compute_day_revenue(self):
        search_payments = self.env['account.payment'].search([])
        search_day_revenue = search_payments.filtered(
            lambda
                x: x.payment_date_confirm.date() == self.todays_date.date() if x.payment_date_confirm else '').mapped(
            'amount')
        self.day_revenue = sum(search_day_revenue)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_revenue(self):
        search_payments = self.env['account.payment'].search([])
        search_mtd_revenue = search_payments.filtered(
            lambda
                x: x.payment_date_confirm.date() <= self.todays_date.date() and x.payment_date_confirm.date() >= self.start_date.date() if x.payment_date_confirm else '').mapped(
            'amount')
        self.mtd_revenue = sum(search_mtd_revenue)

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_revenue(self):
        search_payments = self.env['account.payment'].search([])
        search_ytd_revenue = search_payments.filtered(
            lambda
                x: x.payment_date_confirm.date() <= self.todays_date.date() and x.payment_date_confirm.date() >= self.first_date_year.date() if x.payment_date_confirm else '').mapped(
            'amount')
        self.ytd_revenue = sum(search_ytd_revenue)

    # Walking Function
    @api.depends('todays_date')
    def compute_day_walking(self):
        search_walking = self.env['walking.walking'].search([('walking_date', '=', self.todays_date.date())]).mapped(
            'walking_count')
        if search_walking:
            self.day_walking = sum(search_walking)
        else:
            self.day_walking = False

    @api.depends('todays_date', 'start_date')
    def compute_mtd_walking(self):
        search_walking = self.env['walking.walking'].search(
            [('walking_date', '<=', self.todays_date.date()), ('walking_date', '>=', self.start_date.date())]).mapped(
            'walking_count')
        if search_walking:
            self.mtd_walking = sum(search_walking)
        else:
            self.mtd_walking = False

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_walking(self):
        search_walking = self.env['walking.walking'].search(
            [('walking_date', '<=', self.todays_date.date()),
             ('walking_date', '>=', self.first_date_year.date())]).mapped(
            'walking_count')
        if search_walking:
            self.ytd_walking = sum(search_walking)
        else:
            self.ytd_walking = False

    # Quotation Count
    @api.depends('todays_date')
    def compute_day_quotation_count(self):
        search_quotation = self.env['sale.order'].search(
            [('state', '=', 'sent')])
        search_day_revenue = search_quotation.filtered(
            lambda
                x: x.create_date.date() == self.todays_date.date() if x.create_date else '')
        self.day_quotation_count = len(search_day_revenue)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_quotation_count(self):
        search_quotation = self.env['sale.order'].search(
            [('create_date', '<=', self.todays_date.date()), ('create_date', '>=', self.start_date.date()),
             ('state', '=', 'sent')])
        self.mtd_quotation_count = len(search_quotation)

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_quotation_count(self):
        search_quotation = self.env['sale.order'].search(
            [('create_date', '<=', self.todays_date.date()), ('create_date', '>=', self.first_date_year.date()),
             ('state', '=', 'sent')])
        self.ytd_quotation_count = len(search_quotation)

    # Quotation Value
    @api.depends('todays_date')
    def compute_day_quotation_value(self):
        search_quotation = self.env['sale.order'].search(
            [('state', '=', 'sent')])
        search_day_revenue = search_quotation.filtered(
            lambda
                x: x.create_date.date() == self.todays_date.date() if x.create_date else '').mapped('amount_total')
        self.day_quotation_value = sum(search_day_revenue)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_quotation_value(self):
        search_quotation = self.env['sale.order'].search(
            [('create_date', '<=', self.todays_date.date()), ('create_date', '>=', self.start_date.date()),
             ('state', '=', 'sent')]).mapped('amount_total')
        self.mtd_quotation_value = sum(search_quotation)

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_quotation_value(self):
        search_quotation = self.env['sale.order'].search(
            [('create_date', '<=', self.todays_date.date()), ('create_date', '>=', self.first_date_year.date()),
             ('state', '=', 'sent')]).mapped('amount_total')
        self.ytd_quotation_value = sum(search_quotation)

        # Invoice Value
    @api.depends('todays_date')
    def compute_day_invoice_amount(self):
        search_quotation = self.env['account.move'].search(
            [('move_type', '=', 'out_invoice')])
        search_day_revenue = search_quotation.filtered(
            lambda
                x: x.invoice_date == self.todays_date.date() if x.invoice_date else '').mapped('amount_total')
        self.day_invoice_amount = sum(search_day_revenue)

    @api.depends('todays_date', 'start_date')
    def compute_mtd_invoice_amount(self):
        # serch= self.env['account.move'].search([('move_type','=',)])
        search_quotation = self.env['account.move'].search(
            [('invoice_date', '<=', self.todays_date.date()), ('invoice_date', '>=', self.start_date.date()),
             ('move_type', '=', 'out_invoice')]).mapped('amount_total')
        self.mtd_invoice_amount = sum(search_quotation)

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_invoice_amount(self):
        search_quotation = self.env['account.move'].search(
            [('invoice_date', '<=', self.todays_date.date()), ('invoice_date', '>=', self.first_date_year.date()),
             ('move_type', '=', 'out_invoice')]).mapped('amount_total')
        self.ytd_invoice_amount = sum(search_quotation)

    # Google Rating
    @api.depends('todays_date')
    def compute_day_google_rating(self):
        search_google_rating = self.env['walking.walking'].search([('walking_date', '=', self.todays_date.date())]).mapped(
            'google_rating')
        if search_google_rating:
            self.day_rating = sum(search_google_rating)
        else:
            self.day_rating = False

    @api.depends('todays_date', 'start_date')
    def compute_mtd_google_rating(self):
        search_google_rating = self.env['walking.walking'].search(
            [('walking_date', '<=', self.todays_date.date()), ('walking_date', '>=', self.start_date.date())]).mapped(
            'google_rating')
        if search_google_rating:
            self.mtd_rating = sum(search_google_rating)
        else:
            self.mtd_rating = False

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_google_rating(self):
        search_google_rating = self.env['walking.walking'].search(
            [('walking_date', '<=', self.todays_date.date()),
             ('walking_date', '>=', self.first_date_year.date())]).mapped(
            'google_rating')
        if search_google_rating:
            self.ytd_rating = sum(search_google_rating)
        else:
            self.ytd_rating = False

    # Google Rating
    @api.depends('todays_date')
    def compute_day_follower(self):
        search_follower = self.env['walking.walking'].search(
            [('walking_date', '=', self.todays_date.date())]).mapped(
            'instagram_followers')
        if search_follower:
            self.day_follower = sum(search_follower)
        else:
            self.day_follower = False

    @api.depends('todays_date', 'start_date')
    def compute_mtd_follower(self):
        search_follower = self.env['walking.walking'].search(
            [('walking_date', '<=', self.todays_date.date()),
             ('walking_date', '>=', self.start_date.date())]).mapped(
            'instagram_followers')
        if search_follower:
            self.mtd_follower = sum(search_follower)
        else:
            self.mtd_follower = False

    @api.depends('todays_date', 'first_date_year')
    def compute_ytd_follower(self):
        search_follower = self.env['walking.walking'].search(
            [('walking_date', '<=', self.todays_date.date()),
             ('walking_date', '>=', self.first_date_year.date())]).mapped(
            'instagram_followers')
        if search_follower:
            self.ytd_follower = sum(search_follower)
        else:
            self.ytd_follower = False

    def send_email(self):
        template_id = self.env.ref('custom_homes_to_life.email_template_mtd_report').id
        print("template_id ........", template_id)
        template = self.env['mail.template'].browse(template_id)
        print("template............", template)
        template.send_mail(self.id, force_send=True)
