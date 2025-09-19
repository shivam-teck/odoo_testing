{
    'name': 'PO Accounting- Proforma',
    'version': '1.0',
    'sequence': 1,
    'description': 'Divides payments according to Payment Terms',
    'author': 'Planet Odoo',
    'depends': ['base', 'account', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/templates.xml',
        'views/payment_term_view.xml',
        'views/sale_order_view.xml',
        'views/create_payment_wizard.xml',
        'views/account_payment.xml',
        'wizard/payment_wiz.xml',

        ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}

