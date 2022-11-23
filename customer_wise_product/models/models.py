# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    customer_ids = fields.Many2many('res.partner', string="Customers")

    @api.model
    def create(self, vals):
        res = super(InheritProductTemplate, self).create(vals)
        customer_ids = res.customer_ids
        if customer_ids:
            product_product = self.env['product.product'].search([('product_tmpl_id', '=', res.id)])
            if product_product:
                for rec in product_product:
                    for customer in customer_ids:
                        rec.customer_ids = [(4, customer.id)]
        return res

    def write(self, vals):
        res = super(InheritProductTemplate, self).write(vals)
        if vals.get('customer_ids'):
            product_product = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
            if product_product:
                for rec in product_product:
                    rec.customer_ids = vals.get('customer_ids')
        return res

    def name_get(self):
        result = []
        if self.env.context.get('sale') or (self.env.context.get('move_type') == 'out_invoice'):
            partner_id = self.env.context.get('partner_id')
            products = self.env['product.template'].search([('customer_ids', '=', partner_id)])
            if len(products.ids) > 0:
                for product in products:
                    name = '[%s] %s' % (
                        product.default_code, product.name) if product.default_code else '%s' % product.name
                    result.append((product.id, name))
                return result
            else:
                return result
        else:
            return self.get_normal_result()

    def get_normal_result(self):
        result = []
        for product in self:
            name = '[%s] %s' % (
                product.default_code, product.name) if product.default_code else '%s' % product.name
            result.append((product.id, name))
        return result


class InheritProductProduct(models.Model):
    _inherit = 'product.product'

    customer_ids = fields.Many2many('res.partner', string="Customers")

    def name_get(self):
        result = []
        if self.env.context.get('sale') or (self.env.context.get('move_type') == 'out_invoice'):
            partner_id = self.env.context.get('partner_id')
            products = self.env['product.product'].search([('customer_ids', '=', partner_id)])
            if len(products.ids) > 0:
                for product in products:
                    var_label = self.get_var_label(product)
                    name = '[%s] %s %s' % (
                        product.default_code, product.name, var_label) if product.default_code else '%s %s' % (
                        product.name, var_label) if var_label else '%s' % product.name
                    result.append((product.id, name))
                return result
            else:
                return result
        else:
            return self.get_normal_result()

    @staticmethod
    def get_var_label(product=None):
        labels = []
        for rec in product:
            for label in rec.product_template_variant_value_ids:
                labels.append(label.name)
        return tuple(labels)

    def get_normal_result(self):
        result = []
        for product in self:
            var_label = self.get_var_label(product)
            name = '[%s] %s %s' % (
                product.default_code, product.name, var_label) if product.default_code and var_label else '%s %s' % (
                product.name, var_label) if var_label else '%s' % product.name
            result.append((product.id, name))
        return result
