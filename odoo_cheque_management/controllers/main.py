# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

# 2 :  imports of odoo

import logging

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)


class BankChequeManagement(http.Controller):
    @http.route('/bank/cheque/<model("res.bank"):bank_cheque_id>', type='http', auth="user", website=True)
    def bank_cheque_management(self, bank_cheque_id, **post):
        values = {"bank_cheque_obj": bank_cheque_id}
        return request.render("odoo_cheque_management.bank_cheque_management_template", values)

    @http.route('/bank/cheque/update', type='http', auth="user", website=True)
    def bank_cheque_update_attrs(self, **post):
        is_updated = False
        if post.get("cheque_attribute_line_id"):
            is_updated = request.env["bank.cheque.attribute.line"].browse(
                int(post.get('cheque_attribute_line_id'))).write({
                    "top_displacement": int(post.get("y1", 0)),
                    "left_displacement": int(post.get("x1")) if post.get("x1") else 0,
                    "height": int(post.get("h")) if post.get("h") else 0,
                    "width": int(post.get("w")) if post.get("w") else 0,
                    # "font_size": post.get(""),
                    # "font_family": post.get(""),
                })
        values = {
            "bank_cheque_obj": request.env["res.bank"].browse(int(post.get('bank_cheque_id')))
            if post.get('bank_cheque_id') else False,
        }
        if is_updated:
            values.update({
                "updated_cheque_attribute_line_id": int(post.get('cheque_attribute_line_id'))
            })
        # return self.bank_cheque_management(
        #     bank_cheque_id=values.get("bank_cheque_obj"))
        # post = {}
        # return request.render("odoo_cheque_management.bank_cheque_management_template", values)
        return request.redirect("/bank/cheque/%s" % slug(values.get("bank_cheque_obj")))

    @http.route('/bank/cheque/preview/<model("res.bank"):bank_cheque_id>', type='http', auth="user", website=True)
    def bank_cheque_preview(self, bank_cheque_id, **post):
        values = {"bank_cheque_obj": bank_cheque_id}
        return request.render("odoo_cheque_management.bank_cheque_priview", values)
