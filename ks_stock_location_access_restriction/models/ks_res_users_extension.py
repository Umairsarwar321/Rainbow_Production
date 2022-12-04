# -*- coding: utf-8 -*-

from odoo import api, Command, fields, models, _


class KsResUsersExtension(models.Model):
    _inherit = 'res.users'

    ks_default_location_ids = fields.Many2many('stock.location', string="Default Location")

    def write(self, vals):
        ks_before_write_vals = self.ks_default_location_ids
        res = super(KsResUsersExtension, self).write(vals)
        ks_after_write_vals = self.ks_default_location_ids
        for loc_id in ks_before_write_vals:
            if not loc_id in ks_after_write_vals:
                ks_get_loc_id = self.env['stock.location'].search([('id', '=', loc_id.id)], limit=1)
                ks_get_loc_id.ks_own_user_ids = [Command.unlink(self.env.user.id)]
        return res
