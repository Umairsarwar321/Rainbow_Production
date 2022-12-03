# -*- coding: utf-8 -*-
{
    'name': "Manufacture Reel",

    'summary': """This module is all about manufacturing reels""",

    'description': """
    This module is used to create reels detail which contain sequence number, worker, description and weight
    """,

    'author': "OKLAND",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp', 'stock', 'hr', 'product_development'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/reel_sequence.xml',
        'report/reel_detail_report_action.xml',
        'report/reel_repot_template.xml',
        'report/report_format.xml',
    ],

}
