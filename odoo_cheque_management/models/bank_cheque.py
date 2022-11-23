# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import logging
_logger = logging.getLogger(__name__)

# 2 :  imports of odoo [Imports of odoo]

import odoo
from odoo import api, fields, models, _  # alphabetically ordered
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class BankCheque(models.Model):
    # Private attributes
    _inherit = 'res.bank'

    # Fields declaration
    cheque_image = fields.Binary("Cheque Image")
    cheque_attribute_line_ids = fields.One2many("bank.cheque.attribute.line",
                                                "bank_cheque_id",
                                                "Cheque Attributes")
    cheque_height = fields.Float(string='Cheque Hight',
                                 default=93,
                                 required=True)
    cheque_width = fields.Float(string='Cheque Width',
                                default=203,
                                required=True)
    max_char_in_line1 = fields.Integer(
        "Maximum Characters",
        help="Maximum characters in 'Amount in words Line1' field.\n Aplicable if Cheque attributes has both attributes(Amount In words Line1 & Amount In words Line2)"
    )
    cheque_measure_unit = fields.Selection([("cm", "CM"),
                                            ("in", "Inches"),
                                            ("mm", "MM")],
                                           "Measurement Unit",
                                           default="mm",
                                           required=True)

    def redirect_to_bank_cheque_page(self):
        self.ensure_one()
        if not self.cheque_attribute_line_ids:
            raise UserError(
                _('First you have to set bank cheque attributes. '
                  'Then you will be able to configure attribute(s) values'))
        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url': "/bank/cheque/%s" % self.id,
        }


class BankChequeAttributeLine(models.Model):
    # Private attributes
    _name = 'bank.cheque.attribute.line'
    _description = 'Cheque Attribute Line'

    name = fields.Many2one("bank.cheque.attribute",
                           string='Name',
                           required=True)
    bank_cheque_id = fields.Many2one("res.bank",
                                     string='Bank Cheque',
                                     required=True)
    font_size = fields.Integer(string='Font Size', default=20)
    font_family = fields.Char(string='Font Family')
    letter_spacing = fields.Integer(string='Letter Spacing', default=0)
    top_displacement = fields.Integer(string='Top displacement')
    left_displacement = fields.Integer(string='Left displacement')
    bottom_displacement = fields.Integer(string='Bottom displacement')
    right_displacement = fields.Integer(string='Right displacement')
    height = fields.Integer(string='Height')
    width = fields.Integer(string='Width')

    def reset_values(self):
        for obj in self:
            obj.write({
                "top_displacement": 0,
                "left_displacement": 0,
                "bottom_displacement": 0,
                "right_displacement": 0,
                "height": 0,
                "width": 0,
            })

    @api.onchange("name")
    def onchange_name(self):
        if self.name and self.name.attribute == "cheque_date" and not self.letter_spacing:
            self.letter_spacing = 12


class BankChequeAttribute(models.Model):
    # Private attributes
    _name = 'bank.cheque.attribute'
    _description = 'Bank Cheque Attribute'

    name = fields.Char(string='Name', required=True)
    attribute = fields.Selection(
        [('cheque_date', "Date"), ('pay_line1', "Pay Line 1"),
         ('pay_line2', "Pay Line 2"),
         ('amount_line_1', "Amount Line 1 (in words)"),
         ('amount_line_2', "Amount Line 2 (in words)"),
         ('amount_box', "Amount Box"), ('account_number', "Account Number"),
         ('ac_pay', "A/C Pay Label")],
        required=True)
    demo_data = fields.Char("Demo Data For Preview")
    demo_data_date = fields.Date("Demo Date For Preview",
                                 default=fields.Date.today())
    date_format = fields.Selection([("ddMMyyyy", "DD MM YYYY"),
                                    ("MMddyyyy", "MM DD YYYY")],
                                   "Date Format",
                                   default="ddMMyyyy")


class BankChequeBook(models.Model):
    # Private attributes
    _name = 'bank.cheque.book'
    _description = 'Cheque Attribute Book'

    name = fields.Char("Name", required=True)
    active = fields.Boolean("Active", default=True)
    bank_cheque_id = fields.Many2one("res.bank",
                                     "Bank Cheque",
                                     required=True,
                                     domain="[('cheque_image', '!=', False)]")
    cheque_book_leaves = fields.Integer("Leaves Count",
                                        required=True,
                                        default=20)
    initial_cheque_number = fields.Integer("Initial Cheque Number",
                                           required=True)
    last_cheque_number = fields.Integer("Last Cheque Number")
    account_number = fields.Char(
        "Account Number",
        help="This account number will print on cheque if cheque bank has account number attribute."
    )
    issued_cheque_history_ids = fields.One2many("issued.bank.cheque.history",
                                                "bank_cheque_book_id",
                                                "Issue Cheque History")
    # currency_id = fields.Many2one("res.currency", "Currency")

    def set_cheque_book_number(self):
        for rec in self:
            if rec.cheque_book_leaves and rec.initial_cheque_number:
                rec.last_cheque_number = rec.initial_cheque_number + rec.cheque_book_leaves - 1

    def create_cheque_leaves(self):
        for rec in self:
            if rec.cheque_book_leaves and rec.initial_cheque_number and rec.last_cheque_number:
                i = rec.initial_cheque_number
                for i in range(rec.initial_cheque_number, rec.last_cheque_number + 1, 1):
                    vals = {
                        "cheque_number": i,
                        "bank_cheque_book_id": rec.id
                    }
                    self.env["issued.bank.cheque.history"].create(vals)

    @api.model
    def create(self, vals):
        res = super(BankChequeBook, self).create(vals)
        res.set_cheque_book_number()
        res.create_cheque_leaves()
        return res

    @api.onchange("cheque_book_leaves", "initial_cheque_number")
    def on_change_initial_cheque_number(self):
        self.set_cheque_book_number()

    def btn_create_cheque_leaves(self):
        self.ensure_one()
        if not self.cheque_book_leaves:
            raise UserError(_("Please fill cheque book leaves count first."))
        if not self.initial_cheque_number:
            raise UserError(_("Please fill staring cheque number first."))
        self.create_cheque_leaves()


class IssuesBankChequeHistory(models.Model):
    # Private attributes
    _name = 'issued.bank.cheque.history'
    _description = 'Issued bank cheque'
    _rec_name = "cheque_number"

    state = fields.Selection([('blank', 'Blank'),
                              ('printed', 'Printed'),
                              ('cancelled', 'Cancelled')],
                             "State",
                             default="blank")
    cheque_number = fields.Integer("Cheque Number", required=True)
    customer_id = fields.Many2one("res.partner", "Customer")
    issue_date = fields.Date("Date")
    amount = fields.Float("Amount")
    currency_id = fields.Many2one("res.currency", "Currency")
    issued = fields.Boolean("Cheque Issued")
    bank_cheque_book_id = fields.Many2one("bank.cheque.book",
                                          "Cheque Book",
                                          required=True)
    is_ac_pay = fields.Boolean("A/C Pay Cheque")
    cancelled = fields.Boolean("Cheque Cancelled")
    paid_to = fields.Char("Paid To")

    @api.constrains('cheque_number', 'bank_cheque_book_id')
    def _check_cheque_number_for_bank(self):
        for record in self:
            already_exist = self.search([
                ('cheque_number', '=', record.cheque_number),
                ('bank_cheque_book_id', '=', record.bank_cheque_book_id.id),
            ])
            if len(already_exist) > 1:
                raise ValidationError(
                    _("Cheque number %s is not valid. It has been already used. "
                      "Please use diffrent cheque number.") % record.cheque_number)

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         result.append((record.id, record.bank_cheque_book_id.name + " " + str(record.cheque_number)))
    #     return result

    @api.onchange("cheque_number")
    def on_change_cheque_number(self):
        if self.cheque_number and self.bank_cheque_book_id and self.cheque_number not in range(
                self.bank_cheque_book_id.initial_cheque_number,
                self.bank_cheque_book_id.last_cheque_number + 1, 1):
            raise UserError(
                _("Invalid cheque number. Cheque number should be in range %s to %s (including last number)."
                  ) % (self.bank_cheque_book_id.initial_cheque_number,
                       self.bank_cheque_book_id.last_cheque_number))

    @api.model
    def create(self, vals):
        self.on_change_cheque_number()
        res = super(IssuesBankChequeHistory, self).create(vals)
        return res

    def write(self, vals):
        for rec in self:
            rec.on_change_cheque_number()
        res = super(IssuesBankChequeHistory, self).write(vals)
        return res

    def print_cheque(self):
        self.ensure_one()
        if self.issued:
            raise UserError(
                _("Cheque has been already printed with Cheque number %s" % self.cheque_number))
        # if not self.customer_id or not self.issue_date or self.amount <= 0:
        #     raise UserError(_("One of the field is missing may be Customer, Date or Amount."))
        wizard_id = self.env["invoice.print.bank.cheque.wizard"].create({
            "partner_id": self.customer_id.id,
            "cheque_book_id": self.bank_cheque_book_id.id,
            "cheque_history_id": self.id,
            "pay_name_line1": self.customer_id.name if self.customer_id else self.paid_to,
            "amount": self.amount,
        })
        wizard_id.amount_in_words = wizard_id.currency_id.amount_to_text(wizard_id.amount)
        return {
            'name': _("Print Cheque"),
            'view_mode': 'form',
            'view_id': False,
            'res_model': "invoice.print.bank.cheque.wizard",
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    def do_cancel_cheque(self):
        for obj in self:
            obj.state = "cancelled"


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _prepare_html(self, html):
        bodies, res_ids, header, footer, specific_paperformat_args = super(
            IrActionsReport, self)._prepare_html(html)
        for rec in self:
            if rec.model == "res.bank" and bodies:
                bodies = [
                    bytes(bodies[0].replace(
                        b'class="container"', b'class="" style="margin:0px"').replace(
                            b'class="article o_report_layout_clean"', b'class=""'))
                ]
        return bodies, res_ids, header, footer, specific_paperformat_args
