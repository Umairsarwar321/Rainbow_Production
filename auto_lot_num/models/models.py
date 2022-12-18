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

    for_qty = fields.Integer("Quantity")
    total_gross_weight = fields.Float("Total Gross Wt")
    tare = fields.Float("Tare")
    # tare = fields.Integer("Tare")
    done = fields.Float("Done", compute='_get_done', store=True)
    # done = fields.Integer("Done", compute='_get_done', store=True)
    already_done = fields.Boolean("done")

    @api.depends('total_gross_weight', 'tare')
    def _get_done(self):
        for rec in self:
            rec.done = rec.total_gross_weight - rec.tare

    def generate_lot_num(self):
        for rec in self:
            if rec.picking_id.picking_type_id.code == 'incoming':
                if rec.for_qty:
                    if rec.for_qty <= rec.product_uom_qty:
                        if not rec.for_qty + 1 == len(rec.move_line_ids):
                            last = 0
                            difference = (rec.for_qty + 1) - len(rec.move_line_ids)
                            remaining = rec.product_uom_qty % rec.for_qty
                            all_same = rec.product_uom_qty // rec.for_qty
                            for i in range(difference):
                                lot_number = self.get_lot_number(i + 1)
                                # lot = self.move_line_nosugest_ids
                                tare_qty_old = rec.tare/rec.for_qty
                                product = rec.product_id.categ_id.id

                                # put_putaway = self.env['stock.putaway.rule'].search(['|', ('product_id', '=', rec.product_id.id) ('category_id', '=', rec.product_id.categ_id.id)])
                                put_putaway = self.env['stock.putaway.rule'].search([('category_id', '=', rec.product_id.categ_id.id)])
                                if put_putaway:

                                    line_dict = {'location_dest_id': put_putaway.location_out_id.id,
                                                 'lot_name': lot_number,
                                                 'product_uom_id': rec.product_uom.id,
                                                 'gross_weight': rec.total_gross_weight/rec.for_qty,
                                                 'tare': rec.tare/rec.for_qty,
                                                 'qty_done': (rec.total_gross_weight/rec.for_qty) - (rec.tare/rec.for_qty),
                                                 # 'qty_done': (rec.total_gross_weight/rec.for_qty)-(rec.tare/rec.for_qty),
                                                 'product_id': rec.product_id.id,}
                                    dupli = self.env['stop.lot.duplication']
                                    dupli.create({
                                        "name": line_dict['lot_name']
                                    })
                                    rec.write({
                                        'move_line_ids': [
                                            (0, 0, line_dict)]
                                    })
                                else:
                                    line_dict = {
                                                 'lot_name': lot_number,
                                                 'product_uom_id': rec.product_uom.id,
                                                 'gross_weight': rec.total_gross_weight / rec.for_qty,
                                                 'tare': rec.tare / rec.for_qty,
                                                 'qty_done': (rec.total_gross_weight / rec.for_qty) - (
                                                             rec.tare / rec.for_qty),
                                                 # 'qty_done': (rec.total_gross_weight/rec.for_qty)-(rec.tare/rec.for_qty),
                                                 'product_id': rec.product_id.id, }
                                    dupli = self.env['stop.lot.duplication']
                                    dupli.create({
                                        "name": line_dict['lot_name']
                                    })


                                    rec.write({
                                        'move_line_ids': [
                                            (0, 0, line_dict)]
                                    })
                            # if remaining > 0:
                            #     new_lot = self.get_lot_number(i + 1)
                            #     line_dict.update({
                            #         'qty_done': remaining,
                            #         'lot_name': new_lot
                            #     })
                            #     rec.write({
                            #         'move_line_ids': [
                            #             (0, 0, line_dict)]
                            #     })
                        else:
                            raise UserError(_("Lot number has been assigned to all already"))
                    else:
                        raise UserError(_("For Quantity should be equal or less then demand Quantity"))
                else:
                    raise UserError(_("Please Give The For Quantity"))

    def get_lot_number(self, index=None):
        taken_serial_num = self.move_line_ids.mapped('lot_name')
        date = self.date
        month = date.month
        day = date.day
        initial = str(month) + '-' + str(day) + '-' + '0000000'
        if not index:
            index = ''
        # lot_num = self.product_id.prefix or '' + '-' + initial + str(index)
        lot_num = initial + str(index)
        exists_lot = self.env['stock.production.lot'].search([]).mapped('name')
        stop_duplication = self.env['stop.lot.duplication'].search([]).mapped('name')
        i = 0
        while lot_num in taken_serial_num or lot_num in exists_lot or lot_num in stop_duplication:
            lot_num = initial + str(index + i)
            # lot_num = self.product_id.prefix + '-' + initial + str(index + i)
            i += 1
        return lot_num


class StockMoveLineLotExt(models.Model):
    _inherit = 'stock.move.line'

    gross_weight = fields.Float("Gross Wt")
    tare = fields.Float("Tare")
    # tare = fields.Integer("Tare")


    @api.constrains('lot_name')
    def _check_lot_no(self):

        if not self.lot_name:
            lot_no = self.env['stock.production.lot'].sudo().search([('name', '=', self.lot_name)])
            if lot_no:
                raise UserError(_('Entry with same Lot number already exist in the system.'))


    @api.model
    def create(self, vals_list):
        new_rec = super(StockMoveLineLotExt, self).create(vals_list)
        if new_rec.gross_weight > 0 and new_rec.tare > 0:
            new_rec.qty_done = new_rec.gross_weight - new_rec.tare
        return new_rec



class LotNumberStopDuplicatiton(models.Model):
    _name = 'stop.lot.duplication'

    name = fields.Char()
