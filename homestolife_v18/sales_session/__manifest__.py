{
    'name': 'Sales Session',
    'version': '1.0',
    'sequence': 2,
    'category': '',
    'summary': '',
    'description': """""",
    'author': 'PlanetOdoo',
    'depends': ['base',  'product', 'sale' ],
    "data": [
        "security/ir.model.access.csv",
        "data/session_seq.xml",
        "views/session.xml",
        "views/inherit_sale.xml",
        "views/create_payments_inherit.xml",
    ],
    "assets": {
        "web.assets_backend": [

        ],
        "web.assets_qweb": [

        ],
    },
    'website': 'https://planet-odoo.com/',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}