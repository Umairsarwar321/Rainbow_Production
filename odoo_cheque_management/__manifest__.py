# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name": "Odoo Dynamic Bank Cheque Print",
    "summary": """This module allows you to set various attributes of bank cheque dynamically, so you can print bank cheque in a easy                              manner.""",
    "category": "account",
    "version": "15.0.3",
    "sequence": 1,
    "author": "Webkul Software Pvt. Ltd.",
    "license": "Other proprietary",
    "website": "https://webkul.com/",
    "description": """dynamic cheque, dynamic check, bank check print, check dynamic, bank cheque, cheque dynamic, cheque printing, bank cheque, dynamic print cheque, cheque payment, payment check, Cheque print, check print, check writing, partner cheque print""",
    "live_test_url": "http://odoodemo.webkul.com/?module=odoo_cheque_management&version=13.0",
    "depends": [
        'account',
        'website',
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/cheque_attribute_data.xml',
        'wizard/invoice_print_cheque_transient_views.xml',
        'views/account_invoice_inherit_view.xml',
        'views/bank_cheque_views.xml',
        'views/website_template_view.xml',
        'views/cheque_report.xml',
    ],

    "assets": {
        "website.assets_frontend": {
            "odoo_cheque_management/static/src/js/jquery_Jcrop.js",
            "odoo_cheque_management/static/src/js/bank_cheque.js",
        }},

    "images": ['static/description/Banner.png'],
    "application": True,
    "installable": True,
    "auto_install": False,
    "price": 99,
    "currency": "USD",
    # "pre_init_hook": "pre_init_check",
}
