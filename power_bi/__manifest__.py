# -*- coding: utf-8 -*-
{
    'name': "Power BI Integration",
    'version': '18.0.1.0.0',
    'category': 'Business Intelligence',
    'summary': "Power BI Integration, Odoo Power BI, Business Intelligence Dashboard, Analytics, Reports",
    'description': """
Integrate Microsoft Power BI with Odoo to visualize and analyze your business data.
Create interactive reports and dashboards directly from Odoo using Power BI.
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "www",
    'depends': ['base', 'web', 'mail'],
    'data': [
        'views/power_bi_model_views.xml',  # only XML views, no CSV
        # add other XML files if needed
    ],
    # No demo data at all
    # 'demo': [],  # not required
    'assets': {
        'web.assets_backend': [],
    },
    'images': ['static/description/icon.png'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
}
