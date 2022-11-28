# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restrict Location')

    # stock_location_ids = fields.Many2many(
    #     'stock.location',
    #     'location_security_stock_location_users',
    #     'user_id',
    #     'location_id',
    #     'Stock Locations')

    stock_location_ids = fields.One2many('user.location', 'user_id')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Default Warehouse Operations')

    # @api.constrains('stock_location_ids')
    # def _check_location_ids(self):
    #     if len(self.stock_location_ids.filtered(lambda x: x.is_default)) > 1:
    #         raise ValidationError(_('You cannot set more then one location as default'))
    

    @api.onchange('restrict_locations')
    def _onchange_rewrite_options(self):
        for user in self:
            if not user.restrict_locations:
                user.stock_location_ids = False

    @api.model
    def create(self, values):
        self.env['user.location'].clear_caches()
        return super(ResUsers, self).create(values)

    def write(self, values):
        self.env['user.location'].clear_caches()
        return super(ResUsers, self).write(values)

class UserLocation(models.Model):
    _name = 'user.location'

    is_src =fields.Boolean('Is Src')
    is_dest =fields.Boolean('Is Dest')
    is_default = fields.Boolean('Is Default')
    user_id = fields.Many2one('res.users')
    location_id = fields.Many2one('stock.location', string='Location')

# class stock_move(models.Model):
#     _inherit = 'stock.move'

#     @api.constrains('state', 'location_id', 'location_dest_id')
#     def check_user_location_rights(self):
#         for rec in self:
#             if rec.state == 'draft':
#                 return True
#             user_locations = self.env.user.stock_location_ids.mapped('location_id')
#             if self.env.user.restrict_locations:
#                 message = _(
#                     'Invalid Location. You cannot process this move since you do '
#                     'not control the location "%s". '
#                     'Please contact your Adminstrator.')
#                 if rec.location_id not in user_locations:
#                     raise Warning(message % rec.location_id.name)
#                 elif rec.location_dest_id not in user_locations:
#                     raise Warning(message % rec.location_dest_id.name)


class Product(models.Model):
    _inherit = 'product.product'


    def _get_domain_locations(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = super(Product, self)._get_domain_locations()
        user_location_ids = self.env.user.stock_location_ids.mapped('location_id').ids
        if len(user_location_ids):
            domain_quant_loc += [
                '|', ('location_id', 'in', user_location_ids),
                ('location_id', 'child_of', user_location_ids)
            ]
        return domain_quant_loc, domain_move_in_loc, domain_move_out_loc


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _domain_src_location_id(self):
        if self.env.user.restrict_locations:
            src_loc_ids = self.env.user.stock_location_ids.filtered(lambda x: x.is_src)
            return [('id', 'in', src_loc_ids.mapped('location_id').ids)]
        return [('company_id', 'in', [self.env.company.id, False])]

    @api.model
    def _domain_dest_location_id(self):
        if self.env.user.restrict_locations:
            src_loc_ids = self.env.user.stock_location_ids.filtered(lambda x: x.is_dest)
            return [('id', 'in', src_loc_ids.mapped('location_id').ids)]
        return [('company_id', 'in', [self.env.company.id, False])]

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        domain=lambda self: self._domain_src_location_id())
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        domain=lambda self: self._domain_dest_location_id())

    def check_picking_user_location_rights(self, location_id, origin=False):
        loc_ids = []
        if not origin and not self.env.user.has_group('stock.group_stock_manager') and location_id and location_id not in self.env.user.stock_location_ids.mapped('location_id').ids:
            location = self.env['stock.location'].browse(location_id)
            raise UserError(_('You have no access for (%s) locations, Please contact system administrator!' % location.complete_name))

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('stock.group_stock_manager'):
            self.check_picking_user_location_rights(vals.get('location_id'), vals.get('origin'))
        return super(StockPicking, self).create(vals)

    def write(self, vals):
        if not self.env.user.has_group('stock.group_stock_manager'):
            self.check_picking_user_location_rights(vals.get('location_id'))
        for picking in self.filtered(lambda x: x.picking_type_code == 'incoming' and x.state != 'done'):
            if picking.picking_type_code == 'incoming' and picking.state != 'done' and vals.get('location_dest_id'):
                picking.move_lines.write({'location_dest_id': vals.get('location_dest_id')})
                picking.move_line_ids.write({'location_dest_id': vals.get('location_dest_id')})
        return super(StockPicking, self).write(vals)

    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id:
            self.do_unreserve()
