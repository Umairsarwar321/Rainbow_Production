# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritAccountTax(models.Model):
    _inherit = 'account.tax'

    is_with_holding = fields.Boolean("Is Withholding")


class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    tax_id = fields.Many2one('account.tax', 'Withholding Tax', domain=[('is_with_holding', '=', True)])
    tax_amount = fields.Monetary('Tax Amount', readonyl=True)
    total_amount = fields.Monetary('Total Amount')

    @api.onchange('tax_id', 'total_amount')
    def _calculate_tax_amount(self):
        for rec in self:
            rec.tax_amount = rec.total_amount * (rec.tax_id.amount / 100)
            rec.amount = rec.total_amount - rec.tax_amount

    @api.model
    def create(self, vals_list):
        res = super(InheritAccountPayment, self).create(vals_list)
        if res.tax_amount > 0:
            # new line to append in journal entries
            tax_line = {
                'partner_id': res.partner_id.id if res.partner_id else None,
                'move_id': res.move_id.id,
                'currency_id': res.currency_id.id if res.currency_id else False,
                'name': res.tax_id.name,
                'credit': res.tax_amount,
                'debit': False,
                'account_id': res.tax_id.invoice_repartition_line_ids.account_id.id,
                'quantity': 1,
                'exclude_from_invoice_tab': True,
            }

            # account payable value should be increased also, that's why we get this id
            payable_line = res.move_id.line_ids.filtered(
                lambda line: line.account_internal_type == 'payable'

            )

            # add new value and edit account payable line value
            res.move_id.line_ids = [(1, payable_line.id, {'debit': res.tax_amount + res.amount}), (0, 0, tax_line), ]
            return res
        else:
            return res

    def write(self, vals):
        res = super(InheritAccountPayment, self).write(vals)
        if vals:
            # get the payable line to update
            payable_line = self.move_id.line_ids.filtered(
                lambda line: line.account_internal_type == 'payable'

            )

            # get the tax line to update
            tax_line = self.move_id.line_ids.filtered(
                lambda line: line.account_internal_group == 'liability' and line.account_internal_type == 'other'
            )

            # other line to update the value if needed
            other_line = self.move_id.line_ids.filtered(
                lambda line: line.id not in [payable_line.id, tax_line.id]
            )

            if self.tax_amount == 0:
                # if tax is 0 then make the tax in move_line 0 and unlink and update the payable and other line also
                if tax_line:
                    self.move_id.line_ids = [(1, payable_line.id, {'debit': self.tax_amount + self.amount}),
                                             (1, other_line.id, {'credit': self.amount}),
                                             (1, tax_line.id, {'credit': 0})]
                    tax_line.unlink()
                    return res

                # else change the amount of payable and other line
                else:
                    self.move_id.line_ids = [(1, payable_line.id, {'debit': self.tax_amount + self.amount}),
                                             (1, other_line.id, {'credit': self.amount})]
                    return res

            # if tax line is not presend and tax is not zero then make the tax line in move_line
            if not tax_line:
                tax_line = self.get_tax_line()
                self.move_id.line_ids = [(1, payable_line.id, {'debit': self.tax_amount + self.amount}),
                                         (0, 0, tax_line)]

            # else only update the tax line and payable line other line will be set automatically
            else:
                self.move_id.line_ids = [(1, payable_line.id, {'debit': self.tax_amount + self.amount}),
                                         (1, tax_line.id, {'credit': self.tax_amount})]
        return res

    # get the tax line to make in move_line
    def get_tax_line(self):
        res = self
        tax_line = {
            'partner_id': res.partner_id.id if res.partner_id else None,
            'move_id': res.move_id.id,
            'currency_id': res.currency_id.id if res.currency_id else False,
            'name': res.tax_id.name,
            'credit': res.tax_amount,
            'debit': False,
            'account_id': res.tax_id.invoice_repartition_line_ids.account_id.id,
            'quantity': 1,
            'exclude_from_invoice_tab': True,
        }
        return tax_line
