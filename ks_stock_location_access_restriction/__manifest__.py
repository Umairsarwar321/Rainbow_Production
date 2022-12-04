# -*- coding: utf-8 -*-
{
    'name': "Stock Access Restriction",

    'summary': """
        Stock Access Restriction v15.0""",

    'description': """
        This application provides Odoo users with the feature to apply restrictions on stock location.
        Only those users can access the location who have the permission.
    """,

    'author': "Ksolves India Ltd.",
    'website': "https://store.ksolves.com/",
    'images': ['static/description/Banner.png'],
    'category': 'Stock Management',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        'views/ks_stock_location_extension_view.xml',
        'views/ks_res_users_extension_view.xml',
        'security/security.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
}
