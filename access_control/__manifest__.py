{
    'name': 'Sapat Access Control',
    'version': '1.0',
    'category': 'Access Control & Security',
    'summary': 'User-based menu restrictions for enhanced security and customization in Odoo 18',
    'description': 'Easily restrict or hide specific menu items for individual users in Odoo 18. '
                   'This module allows admins to manage user access to menu items, enhancing control '
                   'and personalization of the user interface.',
    'author': 'Teckzilla',
    'website': "https://www.teckzilla.net/",
    'depends': ['base','web'],
    'data': [
        'security/security.xml',
        'views/res_users_views.xml',
    ],
    "assets": {"web.assets_backend": ["access_control/static/src/components/*"]},
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
