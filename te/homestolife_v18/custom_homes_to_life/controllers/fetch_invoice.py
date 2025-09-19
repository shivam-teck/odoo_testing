from odoo import http
# from odoo.http import request
#
#
# class PaymentData(http.Controller):
#     @http.route(["/sale/"], type="http", auth="public", website="True")
#     def sale_data(self, **post):
#         sales_data = request.env['sale.order'].sudo().search([])
#         values = {
#             'records': sales_data
#         }
#         return request.render("custom_homes_to_life.tmp_sales_data", values)

from odoo.http import request, Response
import xml.etree.ElementTree as ET


class InvoiceController(http.Controller):
    USERNAME = 'girish.joshi@planet-odoo.com'
    PASSWORD = 'htl@123'

    @http.route('/invoice_details', type='http', auth='public')
    def invoice_details(self, start_date, end_date, site_code):
        # username = 'girish.joshi@planet-odoo.com'
        # password = 'htl@123'
        search_company = request.env['res.company'].sudo().search([('site_code', '=', site_code)])

        invoices = request.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('company_id', '=', search_company.id)
        ])
        # print(invoices, 'invoice')
        payments = []
        invoices_xml = False

        if invoices:
            for rec in invoices:
                if rec.invoice_payments_widget:
                    payment = request.env['account.payment'].sudo().search([]).filtered(
                        lambda x: rec in x.reconciled_invoice_ids)
                    payments.append(payment)
                # print(payment, rec, 'hwghj')
                invoices_xml = self._generate_invoices_xml(payments, rec)
            return Response(invoices_xml, content_type='text/xml')
        else:
            pass

    def _generate_invoices_xml(self, invoices, rec):
        root = ET.Element('invoices')
        for invoice in invoices:
            if len(invoice) == 1:
                if invoice.payment_date_confirm:
                    inv_date = invoice.payment_date_confirm.strftime('%Y-%m-%d')
                else:
                    inv_date = False
                if len(invoice.reconciled_invoice_ids) == 1:
                    # print(invoice, 'invoices')
                    amount_total = invoice.reconciled_invoice_ids.mapped('amount_total')
                    amount_untaxed = invoice.reconciled_invoice_ids.mapped('amount_untaxed')
                    tax_amount = amount_total[0] - amount_untaxed[0]
                    # inv_time = invoice.payment_date_confirm.strftime('%H:%M:%S')
                    # tax_amount = invoice.reconciled_invoice_ids.amount_total - invoice.reconciled_invoice_ids.amount_untaxed
                    invoice_element = ET.SubElement(root, 'invoice')
                    # print(invoice.reconciled_invoice_ids.name,'inv name')
                    ET.SubElement(invoice_element, 'Invoice').text = invoice.reconciled_invoice_ids.name if invoice.reconciled_invoice_ids else ''
                    ET.SubElement(invoice_element, 'Invoice_Date').text = str(invoice.reconciled_invoice_ids.invoice_date)
                    ET.SubElement(invoice_element, 'Receipt_number').text = invoice.name
                    ET.SubElement(invoice_element, 'Receipt_Amount').text = str(invoice.amount)
                    ET.SubElement(invoice_element, 'Receipt_Date').text = str(inv_date) if inv_date else False
                    ET.SubElement(invoice_element, 'Invoice_amount').text = str(amount_total[0])
                    ET.SubElement(invoice_element, 'vat_amount').text = str(round(tax_amount, 2))
                    ET.SubElement(invoice_element, 'Net_Sale').text = str(amount_untaxed[0])
                    ET.SubElement(invoice_element, 'Payment_Mode').text = invoice.payment_method_line_id.name
                    ET.SubElement(invoice_element, 'Transaction_status').text = 'SALE'
                else:
                    for inv in invoice.reconciled_invoice_ids:
                        if inv == rec:
                            tax_amount = inv.amount_total - inv.amount_untaxed
                            invoice_element = ET.SubElement(root, 'invoice')
                            ET.SubElement(invoice_element, 'Invoice').text = inv.name
                            ET.SubElement(invoice_element, 'Invoice_Date').text = str(inv.invoice_date)
                            ET.SubElement(invoice_element, 'Receipt_number').text = invoice.name
                            ET.SubElement(invoice_element, 'Receipt_Amount').text = str(invoice.amount)
                            ET.SubElement(invoice_element, 'Receipt_Date').text = str(inv_date) if inv_date else False
                            ET.SubElement(invoice_element, 'Invoice_amount').text = str(inv.amount_total)
                            ET.SubElement(invoice_element, 'vat_amount').text = str(round(tax_amount, 2))
                            ET.SubElement(invoice_element, 'Net_Sale').text = str(inv.amount_untaxed)
                            ET.SubElement(invoice_element, 'Payment_Mode').text = invoice.payment_method_line_id.name
                            ET.SubElement(invoice_element, 'Transaction_status').text = 'SALE'


            elif len(invoice) > 1:
                for i in invoice:
                    if i.payment_date_confirm:
                        inv_date = i.payment_date_confirm.strftime('%Y-%m-%d')
                    else:
                        inv_date = False
                    if len(i.reconciled_invoice_ids) == 1:
                        # print(invoice.reconciled_invoice_ids, 'invoices')
                        amount_total = i.reconciled_invoice_ids.mapped('amount_total')
                        amount_untaxed = i.reconciled_invoice_ids.mapped('amount_untaxed')
                        tax_amount = amount_total[0] - amount_untaxed[0]
                        invoice_element = ET.SubElement(root, 'invoice')
                        ET.SubElement(invoice_element, 'Invoice').text = i.reconciled_invoice_ids.name
                        ET.SubElement(invoice_element, 'Invoice_Date').text = str(i.reconciled_invoice_ids.invoice_date)
                        ET.SubElement(invoice_element, 'Receipt_number').text = i.name
                        ET.SubElement(invoice_element, 'Receipt_Amount').text = str(i.amount)
                        ET.SubElement(invoice_element, 'Receipt_Date').text = str(inv_date) if inv_date else False
                        ET.SubElement(invoice_element, 'Invoice_amount').text = str(amount_total[0])
                        ET.SubElement(invoice_element, 'vat_amount').text = str(round(tax_amount, 2))
                        ET.SubElement(invoice_element, 'Net_Sale').text = str(amount_untaxed[0])
                        ET.SubElement(invoice_element, 'Payment_Mode').text = i.payment_method_line_id.name
                        ET.SubElement(invoice_element, 'Transaction_status').text = 'SALE'
                    else:
                        for inv in invoice.reconciled_invoice_ids:
                            if inv == rec:
                                tax_amount = inv.amount_total - inv.amount_untaxed
                                invoice_element = ET.SubElement(root, 'invoice')
                                ET.SubElement(invoice_element, 'Invoice').text = inv.name
                                ET.SubElement(invoice_element, 'Invoice_Date').text = str(inv.invoice_date)
                                ET.SubElement(invoice_element, 'Receipt_number').text = i.name
                                ET.SubElement(invoice_element, 'Receipt_Amount').text = str(i.amount)
                                ET.SubElement(invoice_element, 'Receipt_Date').text = str(
                                    inv_date) if inv_date else False
                                ET.SubElement(invoice_element, 'Invoice_amount').text = str(inv.amount_total)
                                ET.SubElement(invoice_element, 'vat_amount').text = str(round(tax_amount, 2))
                                ET.SubElement(invoice_element, 'Net_Sale').text = str(inv.amount_untaxed)
                                ET.SubElement(invoice_element,
                                              'Payment_Mode').text = i.payment_method_line_id.name
                                ET.SubElement(invoice_element, 'Transaction_status').text = 'SALE'

        return ET.tostring(root)
