from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class PaymentTermInherit(models.Model):
    _inherit = "account.payment.term"

    def _compute_terms(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount,
                       untaxed_amount_currency, cash_rounding=None):
        """Get the distribution of this payment term.
        :param date_ref: The move date to take into account
        :param currency: the move's currency
        :param company: the company issuing the move
        :param tax_amount: the signed tax amount for the move
        :param tax_amount_currency: the signed tax amount for the move in the move's currency
        :param untaxed_amount: the signed untaxed amount for the move
        :param untaxed_amount_currency: the signed untaxed amount for the move in the move's currency
        :param sign: the sign of the move
        :param cash_rounding: the cash rounding that should be applied (or None).
            We assume that the input total in move currency (tax_amount_currency + untaxed_amount_currency) is already cash rounded.
            The cash rounding does not change the totals: Consider the sum of all the computed payment term amounts in move / company currency.
            It is the same as the input total in move / company currency.
        :return (list<tuple<datetime.date,tuple<float,float>>>): the amount in the company's currency and
            the document's currency, respectively for each required payment date
        """
        self.ensure_one()
        company_currency = company.currency_id
        total_amount = tax_amount + untaxed_amount
        total_amount_currency = tax_amount_currency + untaxed_amount_currency
        rate = abs(total_amount_currency / total_amount) if total_amount else 0.0

        pay_term = {
            'desc': self.line_ids.desc,
            'percent': self.line_ids.value_amount,
            'value': self.line_ids.value,
            'date': self.line_ids._get_due_date(date_ref),
            'has_discount': self.discount_percentage,
            'discount_date': None,
            'discount_amount_currency': 0.0,
            'discount_balance': 0.0,
            'discount_percentage': self.discount_percentage,
            'line_ids': [],
        }

        if self.early_discount:
            # Early discount is only available on single line, 100% payment terms.
            discount_percentage = self.discount_percentage / 100.0
            if self.early_pay_discount_computation in ('excluded', 'mixed'):
                pay_term['discount_balance'] = company_currency.round(
                    total_amount - untaxed_amount * discount_percentage)
                pay_term['discount_amount_currency'] = currency.round(
                    total_amount_currency - untaxed_amount_currency * discount_percentage)
            else:
                pay_term['discount_balance'] = company_currency.round(total_amount * (1 - discount_percentage))
                pay_term['discount_amount_currency'] = currency.round(total_amount_currency * (1 - discount_percentage))

            if cash_rounding:
                cash_rounding_difference_currency = cash_rounding.compute_difference(currency, pay_term[
                    'discount_amount_currency'])
                if not currency.is_zero(cash_rounding_difference_currency):
                    pay_term['discount_amount_currency'] += cash_rounding_difference_currency
                    pay_term['discount_balance'] = company_currency.round(
                        pay_term['discount_amount_currency'] / rate) if rate else 0.0

        residual_amount = total_amount
        residual_amount_currency = total_amount_currency

        for i, line in enumerate(self.line_ids):
            term_vals = {
                'date': line._get_due_date(date_ref),
                'company_amount': 0,
                'foreign_amount': 0,
            }

            # The last line is always the balance, no matter the type
            on_balance_line = i == len(self.line_ids) - 1
            if on_balance_line:
                term_vals['company_amount'] = residual_amount
                term_vals['foreign_amount'] = residual_amount_currency
            elif line.value == 'fixed':
                # Fixed amounts
                term_vals['company_amount'] = sign * company_currency.round(line.value_amount / rate) if rate else 0.0
                term_vals['foreign_amount'] = sign * currency.round(line.value_amount)
            else:
                # Percentage amounts
                line_amount = company_currency.round(total_amount * (line.value_amount / 100.0))
                line_amount_currency = currency.round(total_amount_currency * (line.value_amount / 100.0))
                term_vals['company_amount'] = line_amount
                term_vals['foreign_amount'] = line_amount_currency

            if cash_rounding and not on_balance_line:
                # The value `residual_amount_currency` is always cash rounded (in case of cash rounding).
                #   * We assume `total_amount_currency` is cash rounded.
                #   * We only subtract cash rounded amounts.
                # Thus the balance line is cash rounded.
                cash_rounding_difference_currency = cash_rounding.compute_difference(currency,
                                                                                     term_vals['foreign_amount'])
                if not currency.is_zero(cash_rounding_difference_currency):
                    term_vals['foreign_amount'] += cash_rounding_difference_currency
                    term_vals['company_amount'] = company_currency.round(
                        term_vals['foreign_amount'] / rate) if rate else 0.0

            residual_amount -= term_vals['company_amount']
            residual_amount_currency -= term_vals['foreign_amount']
            pay_term['line_ids'].append(term_vals)

        return pay_term


class PaymentTermLineInherit(models.Model):
    _inherit = "account.payment.term.line"
    _order = "sequence,id"

    desc = fields.Char("Description")
    sequence = fields.Integer(default=10)
