from odoo import models, fields, api


class ProductDevelopment(models.Model):
    _inherit = "product.template"
    _description = "Inherit Product Template"

    unit_width_mm = fields.Float(string="Unit Width (mm)")
    ups = fields.Float(string="Ups")
    print_size_mm = fields.Float(string="Print Size (mm)", compute='_compute_print_size_mm')
    cylinder_length_mm = fields.Integer(string="Cylinder Length (mm)")
    unit_col = fields.Float(string="Unit Col")
    col_repeat = fields.Float(string="Col Repeat")
    circum_dia = fields.Float(string="Circum / Dia", compute='_compute_circum_dia')
    name_type = fields.Char(string="Type")
    art_no = fields.Float(string="Art No.")
    print_side = fields.Char(string="Print Side")
    color = fields.Integer(string="Color")
    cylinder_maker = fields.Many2one('res.partner', string='Cylinder Maker')
    meter_per_kg = fields.Float(string="Meter per kg")

    @api.model
    def create(self, vals):
        res = super(ProductDevelopment, self).create(vals)
        product_product = self.env['product.product'].search([('product_tmpl_id', '=', res.id)])
        if product_product:
            for rec in product_product:
                rec.update({
                    'unit_width_mm': res.unit_width_mm,
                    'ups': res.ups,
                    'print_size_mm': res.print_size_mm,
                    'cylinder_length_mm': res.cylinder_length_mm,
                    'unit_col': res.unit_col,
                    'col_repeat': res.col_repeat,
                    'circum_dia': res.circum_dia,
                    'name_type': res.name_type,
                    'art_no': res.art_no,
                    'print_side': res.print_side,
                    'color': res.color,
                    'cylinder_maker': res.cylinder_maker,
                    'meter_per_kg': res.meter_per_kg,
                })
        return res

    @api.depends('unit_width_mm', 'ups')
    def _compute_print_size_mm(self):
        for rec in self:
            rec.print_size_mm = rec.unit_width_mm * rec.ups

    @api.depends('unit_col', 'col_repeat')
    def _compute_circum_dia(self):
        for record in self:
            record.circum_dia = record.unit_col * record.col_repeat


class InheritProductProduct(models.Model):
    _inherit = "product.product"
    _description = "Inherit Product Template"

    unit_width_mm = fields.Float(string="Unit Width (mm)")
    ups = fields.Float(string="Ups")
    print_size_mm = fields.Float(string="Print Size (mm)", compute='_compute_print_size_mm')
    cylinder_length_mm = fields.Integer(string="Cylinder Length (mm)")
    unit_col = fields.Float(string="Unit Col")
    col_repeat = fields.Float(string="Col Repeat")
    circum_dia = fields.Float(string="Circum / Dia", compute='_compute_circum_dia')
    name_type = fields.Char(string="Type")
    art_no = fields.Float(string="Art No.")
    print_side = fields.Char(string="Print Side")
    color = fields.Integer(string="Color")
    cylinder_maker = fields.Many2one('res.partner', string='Cylinder Maker')
    meter_per_kg = fields.Float(string="Meter per kg")

    @api.depends('unit_width_mm', 'ups')
    def _compute_print_size_mm(self):
        for rec in self:
            rec.print_size_mm = rec.unit_width_mm * rec.ups

    @api.depends('unit_col', 'col_repeat')
    def _compute_circum_dia(self):
        for record in self:
            record.circum_dia = record.unit_col * record.col_repeat
