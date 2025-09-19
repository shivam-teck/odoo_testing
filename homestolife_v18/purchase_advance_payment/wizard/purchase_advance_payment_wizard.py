from odoo import _, api, exceptions, fields, models


class AccountVoucherWizardPurchase(models.TransientModel):
    _name = "account.voucher.wizard.purchase"
    _description = "Account Voucher Wizard Purchase"

    order_id = fields.Many2one("purchase.order", required=True)
    journal_id = fields.Many2one(
        "account.journal",
        "Journal",
        required=True,
        domain=[("type", "in", ("bank", "cash"))],
    )
    journal_currency_id = fields.Many2one(
        "res.currency",
        "Journal Currency",
        store=True,
        readonly=False,
        compute="_compute_get_journal_currency",
    )
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    amount_total = fields.Monetary(readonly=True)
    amount_advance = fields.Monetary(
        "Amount advanced", required=True, currency_field="journal_currency_id"
    )
    date = fields.Date(required=True, default=fields.Date.context_today)
    currency_amount = fields.Monetary(
        "Curr. amount",
        readonly=True,
        currency_field="currency_id",
        compute="_compute_currency_amount",
        store=True,
    )
    payment_ref = fields.Char("Ref.")
    payment_method_id = fields.Many2one(
        'account.payment.method.line',
        string="Payment Method",
        domain="[('id', 'in', available_payment_method_line_ids)]"
    )
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True, tracking=True)

    @api.depends('payment_type', 'journal_id', 'currency_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines(pay.payment_type)
            to_exclude = pay._get_payment_method_codes_to_exclude()
            if to_exclude:
                pay.available_payment_method_line_ids = pay.available_payment_method_line_ids.filtered(lambda x: x.code not in to_exclude)
            print("Available Payment Methods:", pay.available_payment_method_line_ids.mapped('name'))

    def _get_payment_method_codes_to_exclude(self):
        # can be overriden to exclude payment methods based on the payment characteristics
        self.ensure_one()
        return []

    @api.depends("journal_id")
    def _compute_get_journal_currency(self):
        for wzd in self:
            wzd.journal_currency_id = (
                    wzd.journal_id.currency_id.id or self.env.user.company_id.currency_id.id
            )

    @api.constrains("amount_advance")
    def check_amount(self):
        if self.journal_currency_id.compare_amounts(self.amount_advance, 0.0) <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be positive."))
        if self.env.context.get("active_id", False):
            if (
                    self.currency_id.compare_amounts(
                        self.currency_amount, self.order_id.amount_residual
                    )
                    > 0
            ):
                raise exceptions.ValidationError(
                    _("Amount of advance is greater than residual amount on purchase")
                )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        purchase_ids = self.env.context.get("active_ids", [])
        if not purchase_ids:
            return res
        purchase_id = fields.first(purchase_ids)
        purchase = self.env["purchase.order"].browse(purchase_id)
        if "amount_total" in fields_list:
            res.update(
                {
                    "order_id": purchase.id,
                    "amount_total": purchase.amount_residual,
                    "currency_id": purchase.currency_id.id,
                }
            )

        return res

    @api.depends("journal_id", "date", "amount_advance")
    def _compute_currency_amount(self):
        if self.journal_currency_id != self.currency_id:
            amount_advance = self.journal_currency_id._convert(
                self.amount_advance,
                self.currency_id,
                self.order_id.company_id,
                self.date or fields.Date.today(),
            )
        else:
            amount_advance = self.amount_advance
        self.currency_amount = amount_advance

    def _prepare_payment_vals(self, purchase):
        partner_id = purchase.partner_id.id
        return {
            "date": self.date,
            "amount": self.amount_advance,
            "payment_type": "outbound",
            "partner_type": "supplier",
            "memo": f"{self.payment_ref or purchase.name} | OC Number: {purchase.oc_no}",
            "journal_id": self.journal_id.id,
            "currency_id": self.journal_currency_id.id,
            "partner_id": partner_id,
                "payment_method_line_id": self.payment_method_id.id,
        }

    def make_advance_payment(self):
        """Create customer paylines and validate the payment"""
        self.ensure_one()
        payment_obj = self.env["account.payment"]
        purchase_obj = self.env["purchase.order"]

        purchase_ids = self.env.context.get("active_ids", [])
        if purchase_ids:
            purchase_id = fields.first(purchase_ids)
            purchase = purchase_obj.browse(purchase_id)
            payment_vals = self._prepare_payment_vals(purchase)
            payment = payment_obj.sudo().create(payment_vals)
            purchase.account_payment_ids |= payment

            # Move Sale Order and Journal handling inside ho_payment
            self.ho_payment(purchase, payment)

    def ho_payment(self, purchase, payment):
        sale_order = self.env["sale.order"].sudo().search([
            ("name", "=", purchase.partner_ref)
        ], limit=1)

        if not sale_order:
            raise exceptions.UserError(_("No related Sale Order found for this purchase."))

        sale_journal = self.env["account.journal"].sudo().search([
            ("company_id", "=", sale_order.company_id.id),
            ("type", "=", self.journal_id.type),
            ("name", "=", self.journal_id.name)
        ])

        if not sale_journal:
            raise exceptions.UserError(_("No bank/cash journal found for the Sale Order's company."))

        if self.amount_advance <= 0:
            raise exceptions.UserError(_("Payment amount must be greater than zero."))
        if round(self.amount_advance, 2) > self.amount_total:
            raise exceptions.UserError(_("Payment cannot be more than Order Amount."))

        payment_method = self.env['account.payment.method.line'].sudo().search([
            ('journal_id', '=', sale_journal.id),
            ('name', '=', payment.payment_method_line_id.name),
            ('company_id', '=', sale_order.company_id.id)
        ],limit=1)

        payment = self.env['account.payment'].sudo().create({
            'payment_reference': payment.id,
            'partner_id': sale_order.partner_id.id,
            'payment_type': 'inbound',
            'amount': self.amount_advance,
            'date': self.date,
            'memo': "Payment for " + str(self.order_id.name),
            'journal_id': sale_journal.id,
            'payment_method_line_id': payment_method.id,
            'currency_id': self.currency_id.id,
            'order_id': sale_order.id,
            'company_id': sale_order.company_id.id,
        })

        print("HO", payment)

        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': payment.id,
        }

