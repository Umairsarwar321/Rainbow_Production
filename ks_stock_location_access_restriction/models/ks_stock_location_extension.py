# -*- coding: utf-8 -*-

from odoo import api, Command, fields, models, _


class KsStockLocationExtension(models.Model):
    _inherit = 'stock.location'

    ks_is_readonly = fields.Boolean(string="Is Read Only", compute="_compute_is_readonly")
    ks_is_visible = fields.Boolean(string="Is Visible")
    ks_own_user_ids = fields.Many2many('res.users', string="Own Accepted User")
    ks_user_ids = fields.Many2many('res.users', 'ks_accepted_ids', string="Accepted Users",
                                   compute="calculate_ks_user_ids")
    ks_parent_user_ids = fields.Many2many('res.users', 'ks_parent_user_ids', string="Parent Location Users")

    @api.onchange('ks_own_user_ids')
    def calculate_own_user_ids(self):
        if self.ks_own_user_ids:
            self.ks_is_visible = True
        else:
            self.ks_is_visible = False
        self.ks_user_ids = [Command.clear()]
        self.ks_parent_user_ids = [Command.clear()]
        for rec_id in self.ks_own_user_ids:
            if not rec_id in self.ks_user_ids:
                self.ks_user_ids = [Command.link(rec_id.id)]
                self.ks_parent_user_ids = [Command.link(rec_id.id)]
        ks_child_ids = self.env['stock.location'].browse(self.location_id.id)
        if ks_child_ids.ks_own_user_ids:
            for rec in ks_child_ids.ks_own_user_ids:
                if not rec in self.ks_user_ids:
                    self.ks_user_ids = [Command.link(rec.id)]
                    self.ks_parent_user_ids = [Command.link(rec.id)]

    def calculate_ks_user_ids(self):
        self.ks_user_ids = [Command.clear()]
        self.ks_parent_user_ids = [Command.clear()]
        if 22 in self.env.user.groups_id.ids:
            if self.ks_own_user_ids:
                self.ks_own_user_ids = [Command.link(self.env.user.id)]
        if self.ks_own_user_ids:
            if self.location_id:
                ks_child_ids = self.env['stock.location'].browse(self.location_id.id)
                if ks_child_ids.ks_own_user_ids:
                    for rec in ks_child_ids.ks_own_user_ids:
                        if not rec in self.ks_user_ids:
                            self.ks_user_ids = [Command.link(rec.id)]
                            self.ks_parent_user_ids = [Command.link(rec.id)]
                else:
                    self.ks_user_ids = Command.link(0)
            if self.ks_own_user_ids:
                for ks_own_user_id in self.ks_own_user_ids:
                    self.ks_user_ids = [Command.link(ks_own_user_id.id)]
                    self.ks_parent_user_ids = [Command.link(ks_own_user_id.id)]
        else:
            self.ks_user_ids = [Command.link(0)]

    @api.onchange('usage')
    def _compute_is_readonly(self):
        if self.usage == 'internal':
            self.ks_is_readonly = False
        else:
            self.ks_is_readonly = True
