# -*- coding: utf-8 -*-
{
    'name': "Power BI Integration",
    'version': '18.0.1.0.0',
    'category': 'Business Intelligence',
    'summary': """Power BI Integration, Odoo Power BI, Business Intelligence Dashboard, Analytics, Reports""",
    'description': """Integrate Microsoft Power BI with Odoo to visualize and analyze your business data.
    Create interactive reports and dashboards directly from Odoo using Power BI""",
    'live_test_url': ',',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "www",
    'depends': ['base','web','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/power_bi_model_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js',
            'powerbi_integration/static/src/css/**/*.css',
            'powerbi_integration/static/src/js/**/*.js',
            'powerbi_integration/static/src/xml/**/*.xml',
        ],
    },
    'images': ['static/description/icon.png'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
}
