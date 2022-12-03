from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ManufacturingModelInherit(models.Model):
    _inherit = 'mrp.production'

    production_in_meters = fields.Float('Production In Meters')
    no_of_reels = fields.Integer('No. of Reels')
    reel_detail_ids = fields.One2many('reel.detail', 'mrp_id')
    manufacturing_cylinder_ids = fields.One2many('manufacturing.cylinder', 'mrp_cylinder_id')
    hide_button = fields.Boolean("Hide Button", default=False)

    # This function is used to create manufacturing reel detail
    def create_reel(self):
        if not self.no_of_reels:
            raise ValidationError('Please add at least one reel detail')
        elif not self.lot_producing_id:
            raise ValidationError('Please first create lot serial number !')
        else:
            for line in range(int(self.no_of_reels)):
                self.reel_detail_ids = [(0, 0, {'sequence_no': self.lot_producing_id.name + '-' + str(line + 1)})]
            self.hide_button = True

    @api.onchange("move_raw_ids")
    def onchange_consumed(self):
        for line in self.move_raw_ids:
            if line.quantity_done:
                line.meter = line.quantity_done * line.product_id.meter_per_kg
            line.meter = line.product_id.meter_per_kg

    @api.depends('workorder_ids.state', 'move_finished_ids', 'move_finished_ids.quantity_done')
    def _get_produced_qty(self):
        res = super(ManufacturingModelInherit, self)._get_produced_qty()
        for rec in self:
            for line in rec.move_raw_ids:
                line.meter = line.quantity_done * line.product_id.product_tmpl_id.meter_per_kg
        return res


class StackMoveModelInherit(models.Model):
    _inherit = 'stock.move'

    meter = fields.Integer(string="Meter")


class WorkOrderModelInherit(models.Model):
    _inherit = 'mrp.workorder'

    workers_id = fields.Many2one('hr.employee', string="Worker")
    weight = fields.Float(string="Weight")
    meter = fields.Float(string="Meter")


# reel detail model defined here
class ReelDetail(models.Model):
    _name = 'reel.detail'

    sequence_no = fields.Char('Sequence')
    worker_id = fields.Many2one('res.partner', 'Worker')
    weight = fields.Float('Weight')
    description = fields.Text('Description')
    mrp_id = fields.Many2one('mrp.production')


class StackMoveModelInherit(models.Model):
    _inherit = 'stock.move'

    meter = fields.Integer(string="Meter")


class MrpWorkCenterModelInherit(models.Model):
    _inherit = 'mrp.workcenter'

    cylinder_new = fields.Boolean(string="Cylinder")


# manufacturing cylinder model defined here
class ManufacturingCylinderModel(models.Model):
    _name = "manufacturing.cylinder"

    cylinder = fields.Char(string="Cylinder")
    job_code = fields.Char(string="Job Code")
    job_name = fields.Char(string="Job Name")
    mrp_cylinder_id = fields.Many2one('mrp.production')
