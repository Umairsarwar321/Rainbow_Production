import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class stock_gatepass(models.Model):
    _name = 'stock.gatepass'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Gate Pass'
    _order = "name desc"

    name = fields.Char('Name', size=256, readonly=True, tracking=True, copy=False)
    visitor_name = fields.Char('Name', required=True)
    phone_number = fields.Char()
    reasone = fields.Char('Reason')
    email = fields.Char()
    visitor_company = fields.Many2one('res.company')
    time_in = fields.Datetime('Date Time In')
    time_out = fields.Datetime('Date Time Out')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    department_id = fields.Many2one('hr.department', 'Department')
    created_by_id = fields.Many2one('res.users', 'Created By')
    company_id = fields.Many2one('res.company', 'Company')
    picking_id = fields.Many2one('stock.picking', 'Picking', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], 'States', tracking=True, default='draft')
    line_ids = fields.One2many('stock.gatepass.line', 'gatepass_id', 'Products', readonly=True,
                               states={'draft': [('readonly', False)]})
    picking_ref = fields.Char('Picking Reference')
    origin = fields.Char('Source Document')
    type = fields.Selection([('in', 'In'), ('out', 'Out')])
    so_ref = fields.Char('Sale Reference')
    partner_id = fields.Many2one('res.partner')

    @api.model
    def create(self, vals):
        if vals.get('name', False) is False:
            if vals.get('type', False) == 'out':
                vals['name'] = self.env.ref('stock_gatepass.seq_gate_pass_outward').next_by_id()
            elif vals.get('type', False) == 'in':
                vals['name'] = self.env.ref('stock_gatepass.seq_gate_pass').next_by_id()
        return super(stock_gatepass, self).create(vals)

    def action_confirm(self):
        self.state = 'confirm'


class stock_gatepass_line(models.Model):
    _name = 'stock.gatepass.line'
    _description = 'Gate Pass Lines'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    gatepass_id = fields.Many2one('stock.gatepass', 'Gate Pass', required=True)
    product_qty = fields.Float('Quantity', required=True)
    gate_in_qty = fields.Float('Gate In Quantity')
    gate_out_qty = fields.Float('Gate Out Quantity')


class GatePassWizard(models.TransientModel):
    _name = 'gate.pass.wizard'

    visitor_name = fields.Char('Name', required=True)
    phone_number = fields.Char()
    employee_id = fields.Many2one('hr.employee', 'Employee')
    department_id = fields.Many2one('hr.department', 'Department')
    created_by_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    time_out = fields.Datetime()
    picking_ref = fields.Char('Picking Reference')
    picking_type_code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'), ('internal', 'Internal')])
    origin = fields.Char('Source Document')
    reasone = fields.Char('Reason')

    @api.model
    def default_get(self, fields):
        res = super(GatePassWizard, self).default_get(fields)
        res.update({'time_out': datetime.datetime.now()})
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.department_id = self.employee_id.department_id.id

    def generate_gatepass(self):
        product_arr = []
        picking = self.env['stock.picking'].browse(self._context.get('active_ids', []))
        for operation in picking.move_line_ids:
            product_arr.append((0, 0, {'product_id': operation.product_id.id, 'product_qty': operation.product_qty}))
        vals = {
            'visitor_name': self.visitor_name, 'phone_number': self.phone_number, 'employee_id': self.employee_id.id,
            'department_id': self.department_id.id, 'created_by_id': self.created_by_id.id,
            'company_id': self.company_id.id, 'reasone': self.reasone, 'state': 'draft', 'line_ids': product_arr,
            'picking_ref': self.picking_ref, 'origin': self.origin, 'partner_id': picking.partner_id.id
        }
        gate_pass_id = self.env['stock.gatepass'].create(vals)
        if picking.picking_type_code == 'outgoing':
            gate_pass_id.write(
                {'name': self.env.ref('stock_gatepass.seq_gate_pass_outward').next_by_id(), 'time_out': self.time_out,
                 'type': 'out'})
            picking.write({'gatepass_out_id': gate_pass_id.id})
        elif picking.picking_type_code == 'incoming':
            gate_pass_id.write(
                {'name': self.env.ref('stock_gatepass.seq_gate_pass').next_by_id(), 'time_in': self.time_out,
                 'type': 'in'})
            picking.write({'gate_pass_id': gate_pass_id.id})


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    gate_pass_id = fields.Many2one('stock.gatepass', 'Gate Pass In', copy=False)
    inspection_id = fields.Many2one('product.inspection', 'Inspection', copy=False)
    gatepass_out_id = fields.Many2one('stock.gatepass', 'Gate Pass Out', copy=False)
    is_visible_gatepass_out = fields.Boolean('Is Visible?', compute='_compute_is_visible_gatepass_out')

    @api.depends('inspection_id.line_ids')
    def _compute_is_visible_gatepass_out(self):
        self.is_visible_gatepass_out = any(
            True if record.rejected_qty > 0 else False for record in self.inspection_id.line_ids)

    def button_validate(self):
        if (
                self.picking_type_code == 'outgoing' and not self.gatepass_out_id or self.picking_type_code == 'incoming') and not self.gate_pass_id and self.env.company.id not in [
            1, 2]:
            raise UserError('You cannot validate picking without validating gatepass!')
        else:
            return super(StockPicking, self).button_validate()

    def create_inspection(self):
        if self.gate_pass_id.state == 'draft':
            raise UserError('You won\'t be able to create inspection without validating the gatepass!')
        else:
            product_arr = []
            for record in self.gate_pass_id.line_ids:
                product_arr.append((0, 0, {'product_id': record.product_id.id, 'gate_in_qty': record.gate_in_qty}))
            inspection = self.env['product.inspection'].create(
                {'picking_ref': self.id, 'po_ref': self.origin if self.picking_type_code == 'incoming' else False,
                 'gatepass_ref': self.gate_pass_id.name, 'state': 'draft', 'line_ids': product_arr})
            self.write({'inspection_id': inspection.id})

    def generate_gatepass_out(self):
        if self.picking_type_code == 'outgoing':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Create Gate Pass',
                'res_model': 'gate.pass.wizard',
                'view_mode': 'form',
                'context': {'default_visitor_name': self.partner_id.name, 'default_picking_ref': self.name,
                            'default_origin': self.origin, 'default_picking_type_code': self.picking_type_code},
                'target': 'new'
            }
        elif self.picking_type_code == 'incoming':
            self.gatepass_out_id = self.gate_pass_id.copy()
            self.gatepass_out_id.name = self.env.ref('stock_gatepass.seq_gate_pass_outward').next_by_id()
            self.gatepass_out_id.state = 'draft'
            for inspection_line in self.inspection_id.line_ids.filtered(lambda record: record.rejected_qty > 0):
                vals = {'product_id': inspection_line.product_id.id, 'product_qty': inspection_line.rejected_qty,
                        'gatepass_id': self.gatepass_out_id.id}
                self.env['stock.gatepass.line'].create(vals)

    def create_gatepass(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Gate Pass',
            'res_model': 'gate.pass.wizard',
            'view_mode': 'form',
            'context': {'default_visitor_name': self.partner_id.name, 'default_picking_ref': self.name,
                        'default_origin': self.origin, 'default_picking_type_code': self.picking_type_code},
            'target': 'new'
        }


class ProductInspection(models.Model):
    _name = 'product.inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(readonly=True, default=lambda self: _('New'))
    picking_ref = fields.Many2one('stock.picking', 'Picking')
    po_ref = fields.Char('Purchase Reference')
    gatepass_ref = fields.Char('GatePass Reference')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], 'States', tracking=True, default='draft')
    line_ids = fields.One2many('product.inspection.line', 'inspection_id', 'Products')
    reasone = fields.Char('Reason')

    def action_confirm(self):
        self.state = 'confirm'

    @api.model
    def create(self, vals):
        if vals.get('name', False) is False:
            vals.update({'name': self.env.ref('stock_gatepass.seq_inspection').next_by_id()})
        return super(ProductInspection, self).create(vals)


class ProductInspectionLine(models.Model):
    _name = 'product.inspection.line'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    inspection_id = fields.Many2one('product.inspection', required=True)
    gate_in_qty = fields.Float('Gate In Quantity')
    accepted_qty = fields.Float('Accepted Qty')
    rejected_qty = fields.Float(compute='_compute_rejected_qty', string='Rejected Qty')

    @api.depends('gate_in_qty', 'accepted_qty')
    def _compute_rejected_qty(self):
        for record in self:
            record.rejected_qty = record.gate_in_qty - record.accepted_qty


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.constrains('move_line_nosuggest_ids')
    def _check_move_lines(self):
        if self.picking_id.picking_type_code == 'incoming':
            inspection_qty = self.picking_id.inspection_id.line_ids.filtered(
                lambda record: record.product_id == self.product_id).accepted_qty
            if sum(self.move_line_nosuggest_ids.mapped('qty_done')) > inspection_qty:
                raise UserError('Qty can not be more than inspection qty!')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('location_dest_id')
    def _onchange_location_dest_id(self):
        if self.picking_id.picking_type_code == 'incoming':
            self.qty_done = self.picking_id.inspection_id.line_ids.filtered(
                lambda record: record.product_id == self.product_id).accepted_qty
