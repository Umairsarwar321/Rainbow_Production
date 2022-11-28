# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InheritProductProduct(models.Model):
    _inherit = 'product.product'
    _sql_constraints = [
        ('prefix', 'UNIQUE (prefix)',
         'Prefix Must Be Unique.'),
    ]

    prefix = fields.Char("Prefix")


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    prefix = fields.Char("Prefix")

    # @api.model
    # def create(self, vals):
    #     res = super(InheritProductTemplate, self).create(vals)
    #     product_product = self.env['product.product'].search([('product_tmpl_id', '=', res.id)])
    #     if product_product:
    #         for rec in product_product:
    #             rec.prefix = res.prefix
    #     return res
    #
    # def write(self, vals):
    #     res = super(InheritProductTemplate, self).write(vals)
    #     if vals.get('prefix'):
    #         product_product = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
    #         if product_product:
    #             for rec in product_product:
    #                 rec.prefix = vals.get('prefix')
    #     return res


class InheritStockMove(models.Model):
    _inherit = "stock.move"

    for_qty = fields.Integer("For Qty")
    already_done = fields.Boolean("done")

    def generate_lot_num(self):
        for rec in self:
            if rec.for_qty:
                if rec.for_qty <= rec.product_uom_qty:
                    if not rec.for_qty + 1 == len(rec.move_line_ids):
                        last = 0
                        difference = (rec.for_qty + 1) - len(rec.move_line_ids)
                        remaining = rec.product_uom_qty % rec.for_qty
                        all_same = rec.product_uom_qty // rec.for_qty
                        for i in range(difference):
                            lot_number = self.get_lot_number(i + 1)
                            line_dict = {'lot_name': lot_number,
                                         'product_uom_id': rec.product_uom.id,
                                         'product_id': rec.product_id.id, 'qty_done': all_same}
                            rec.write({
                                'move_line_ids': [
                                    (0, 0, line_dict)]
                            })
                        if remaining > 0:
                            new_lot = self.get_lot_number(i + 1)
                            line_dict.update({
                                'qty_done': remaining,
                                'lot_name': new_lot
                            })
                            rec.write({
                                'move_line_ids': [
                                    (0, 0, line_dict)]
                            })
                    else:
                        raise UserError(_("Lot number has been assigned to all already"))
                else:
                    raise UserError(_("For Quantity should be equal or less then demand Quantity"))
            else:
                raise UserError(_("Please Give The For Quantity"))

    def get_lot_number(self, index=None):
        taken_serial_num = self.move_line_ids.mapped('lot_name')
        initial = '000'
        lot_num = self.product_id.prefix + '-' + initial + str(index)
        exists_lot = self.env['stock.production.lot'].search([]).mapped('name')
        i = 0
        while lot_num in taken_serial_num or lot_num in exists_lot:
            lot_num = self.product_id.prefix + '-' + initial + str(index + i)
            i += 1
        return lot_num
