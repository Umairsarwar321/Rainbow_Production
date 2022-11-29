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

    @api.depends('unit_width_mm', 'ups')
    def _compute_print_size_mm(self):
        for rec in self:
            rec.print_size_mm = rec.unit_width_mm * rec.ups

    @api.depends('unit_col', 'col_repeat')
    def _compute_circum_dia(self):
        for record in self:
            record.circum_dia = record.unit_col * record.col_repeat
