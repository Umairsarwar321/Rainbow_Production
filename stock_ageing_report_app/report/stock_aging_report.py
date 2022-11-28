# -*- coding: utf-8 -*-


from datetime import datetime, timedelta
from odoo import models, api, fields
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_round


class StockAgingReport(models.AbstractModel):
    _name = 'report.stock_ageing_report_app.report_stockaginginfo'
    _description = 'Stock Aging Report'

    def _get_columns(self, data):
        period_length = data.get('period_length')
        column_data = []
        current_period_lenth = 0
        for i in range(0, 5):
            col = str(current_period_lenth) + "-" + str(current_period_lenth + period_length)
            current_period_lenth += period_length
            column_data.append(col)
        col = "> " + str(current_period_lenth)
        column_data.append(col)
        return column_data

    def _get_date_data(self, datas):
        start_date = False
        end_date = False
        date_data = []
        for i in range(0, 6):
            data = {}
            if i <= 0:
                start_date = datas.get('start_date')
                end_date = (datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)) + timedelta(
                    days=datas.get('period_length'))
                if isinstance(start_date, datetime):
                    start_date = datetime.strftime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                if isinstance(end_date, datetime):
                    end_date = datetime.strftime(end_date, DEFAULT_SERVER_DATE_FORMAT)
                data.update({'start_date': start_date, 'end_date': end_date})
                date_data.append(data)
                start_date = (datetime.strptime(datas.get('start_date'), DEFAULT_SERVER_DATE_FORMAT))
            else:
                start_date = start_date + timedelta(days=datas.get('period_length'))
                end_date = end_date + timedelta(days=datas.get('period_length'))
                if isinstance(start_date, datetime):
                    start_date = datetime.strftime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                if isinstance(end_date, datetime):
                    end_date = datetime.strftime(end_date, DEFAULT_SERVER_DATE_FORMAT)
                data.update({'start_date': start_date, 'end_date': end_date})
                date_data.append(data)
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
        return date_data

    # Warehouse

    def _get_product_info(self, product_id, warehouse_id, start_date, end_date, usage, code, name, is_last, company_id):
        if not is_last:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and date<=%s and picking_type_id is not null and location_dest_id in (select id from stock_location where usage=%s) and picking_type_id in (select id from stock_picking_type where warehouse_id=%s and code=%s and name=%s) and company_id=%s",
                (product_id, start_date, end_date, usage, warehouse_id, code, name, company_id))
        else:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and picking_type_id is not null and location_dest_id in (select id from stock_location where usage=%s) and picking_type_id in (select id from stock_picking_type where warehouse_id=%s and code=%s and name=%s) and company_id=%s",
                (product_id, start_date, usage, warehouse_id, code, name, company_id))
        result = self.env.cr.fetchone()[0]
        if result:
            return result
        else:
            return 0.0

    def _get_product_in_info(self, product_id, warehouse_id, start_date, end_date, usage, code, name, is_last,
                             company_id):
        if not is_last:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and date<=%s and picking_type_id is not null and origin_returned_move_id is null and location_dest_id in (select id from stock_location where usage='internal') and warehouse_id=%s and company_id=%s",
                (product_id, start_date, end_date, warehouse_id, company_id))
        else:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and picking_type_id is not null and origin_returned_move_id is null and location_dest_id in (select id from stock_location where usage='internal') and warehouse_id=%s and company_id=%s",
                (product_id, start_date, warehouse_id, company_id))
        result = self.env.cr.fetchone()[0]
        if result:
            return result
        else:
            return 0.0

    def _get_return_in_qty(self, product_id, warehouse_id, start_date, end_date, code, name, is_last, company_id):
        if not is_last:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and date<=%s and origin_returned_move_id is not null and location_dest_id in (select id from stock_location where usage='internal') and warehouse_id=%s and company_id=%s",
                (product_id, start_date, end_date, warehouse_id, company_id))
        else:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and origin_returned_move_id is not null and location_dest_id in (select id from stock_location where usage='internal') and warehouse_id=%s and company_id=%s",
                (product_id, start_date, warehouse_id, company_id))
        result = self.env.cr.fetchone()[0]
        if result:
            return result
        else:
            return 0.0

    def _get_return_out_qty(self, product_id, warehouse_id, start_date, end_date, code, name, is_last, company_id):
        if not is_last:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and date<=%s and origin_returned_move_id is not null and location_dest_id in (select id from stock_location where usage='supplier') and warehouse_id=%s and company_id=%s",
                (product_id, start_date, end_date, warehouse_id, company_id))
        else:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and origin_returned_move_id is not null and location_dest_id in (select id from stock_location where usage='supplier') and warehouse_id=%s and company_id=%s",
                (product_id, start_date, warehouse_id, company_id))
        result = self.env.cr.fetchone()[0]
        if result:
            return result
        else:
            return 0.0

    def _get_adjusted_qty(self, product_id, warehouse_id, start_date, end_date, is_last, company_id):
        ad_in_qty = 0.0
        ad_out_qty = 0.0
        if not is_last:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and date<=%s and picking_type_id is null and location_dest_id = (select default_location_dest_id from stock_picking_type where warehouse_id=%s and code=%s and name=%s) and company_id=%s",
                (product_id, start_date, end_date, warehouse_id, 'incoming', 'Receipts', company_id))
        else:
            self.env.cr.execute(
                "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and picking_type_id is null and location_dest_id = (select default_location_dest_id from stock_picking_type where warehouse_id=%s and code=%s and name=%s) and company_id=%s",
                (product_id, start_date, warehouse_id, 'incoming', 'Receipts', company_id))
        adjust_in_qty = self.env.cr.fetchone()[0]
        if adjust_in_qty:
            ad_in_qty = adjust_in_qty
        else:
            ad_in_qty = 0.0

        self.env.cr.execute(
            "select sum(product_uom_qty) from stock_move where product_id=%s and state='done' and date>=%s and date<=%s and picking_type_id is null and location_id = (select default_location_src_id from stock_picking_type where warehouse_id=%s and code=%s and name=%s) and company_id=%s",
            (product_id, start_date, end_date, warehouse_id, 'outgoing', 'Delivery Orders', company_id))

        adjust_out_qty = self.env.cr.fetchone()[0]
        if adjust_out_qty:
            ad_out_qty = adjust_out_qty
        else:
            ad_out_qty = 0.0
        adjustment_qty = ad_in_qty - ad_out_qty
        return adjustment_qty

    def _get_warehouse_details(self, data, warehouse):
        lines = []
        if warehouse:
            start_date_data = data.get('start_date')
            category_ids = data.get('category_ids')
            filter_type = data.get('filter_type')
            product_ids = data.get('product_ids')
            company = data.get('company_id')
            if filter_type == 'category':
                product_ids = self.env['product.product'].search([('categ_id', 'in', category_ids.ids)])
            else:
                product_ids = self.env['product.product'].search([('id', 'in', product_ids.ids)])
            product_data = []
            for product_id in product_ids:
                value = {}
                counter = 1
                col = "col_"
                if product_id.product_template_attribute_value_ids:
                    variant = product_id.product_template_attribute_value_ids._get_combination_name()
                    name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
                    product_name = name
                else:
                    product_name = product_id.name
                value.update({
                    'product_id': product_id.id,
                    'product_name': product_name or '',
                    'product_code': product_id.default_code or '',
                    'cost_price': product_id.standard_price or 0.00,
                })
                is_last = False
                for date_data in self._get_date_data(data):
                    if counter == 6:
                        is_last = True
                    start_date = date_data.get('start_date')
                    end_date = date_data.get('end_date')
                    warehouse_id = warehouse.id
                    company_id = company.id
                    delivered_qty = self._get_product_info(product_id.id, warehouse_id, start_date, end_date,
                                                           'customer', 'outgoing', 'Delivery Orders', is_last,
                                                           company_id)
                    received_qty = self._get_product_in_info(product_id.id, warehouse_id, start_date, end_date,
                                                             'internal', 'incoming', 'Receipts', is_last, company_id)
                    return_in_qty = self._get_return_in_qty(product_id.id, warehouse_id, start_date, end_date,
                                                            'outgoing', 'Delivery Orders', is_last, company_id)
                    return_out_qty = self._get_return_out_qty(product_id.id, warehouse_id, start_date, end_date,
                                                              'incoming', 'Receipts', is_last, company_id)
                    adjusted_qty = self._get_adjusted_qty(product_id.id, warehouse_id, start_date, end_date, is_last,
                                                          company_id)
                    qty_on_hand = (received_qty + adjusted_qty + return_in_qty) - (delivered_qty - return_out_qty)
                    qty_hand_key = col + str(counter)
                    value.update({qty_hand_key: qty_on_hand})
                    counter += 1
                product_data.append(value)
            lines.append({'product_data': product_data})
        return lines

    # Location

    def _get_product_location_info(self, product_id, start_date, end_date, is_last, location_id, company_id):
        result = 0.0
        domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
        if not is_last:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('date', '<=', end_date),
                             ('picking_type_id.code', '=', 'outgoing')]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        else:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('picking_type_id.code', '=', 'outgoing')]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        return result

    def _get_product_location_in_info(self, product_id, start_date, end_date, is_last, location_id, company_id):
        result = 0.0
        domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
        if not is_last:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('date', '<=', end_date),
                             ('picking_type_id.code', '=', 'incoming')]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        else:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('picking_type_id.code', '=', 'incoming')]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        return result

    def _get_return_location_in_qty(self, product_id, start_date, end_date, is_last, location_id, company_id):
        result = 0.0
        domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
        if not is_last:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('date', '<=', end_date),
                             ('picking_type_id.code', '=', 'incoming'), ('origin_returned_move_id', '!=', False)]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        else:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('picking_type_id.code', '=', 'incoming'),
                             ('origin_returned_move_id', '!=', False)]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        return result

    def _get_return_location_out_qty(self, product_id, start_date, end_date, is_last, location_id, company_id):
        result = 0.0
        domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
        if not is_last:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('date', '<=', end_date),
                             ('picking_type_id.code', '=', 'outgoing'), ('origin_returned_move_id', '!=', False)]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        else:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('picking_type_id.code', '=', 'outgoing'),
                             ('origin_returned_move_id', '!=', False)]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        return result

    def _get_adjusted_location_qty(self, product_id, start_date, end_date, is_last, location_id, company_id):
        result = 0.0
        domain_quant = [('product_id', '=', product_id), ('state', '=', 'done'), ('company_id', '=', company_id)]
        if not is_last:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('date', '<=', end_date), ('picking_type_id', '=', False)]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        else:
            domain_quant += ['|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)]
            domain_quant += [('date', '>=', start_date), ('picking_type_id', '=', False)]
            move_ids = self.env['stock.move'].search(domain_quant)
            result = sum([x.product_uom_qty for x in move_ids])
        return result

    def _get_location_details(self, data, location):
        lines = []
        if location:
            start_date_data = data.get('start_date')
            category_ids = data.get('category_ids')
            filter_type = data.get('filter_type')
            product_ids = data.get('product_ids')
            company = data.get('company_id')
            if filter_type == 'category':
                product_ids = self.env['product.product'].search([('categ_id', 'in', category_ids.ids)])
            else:
                product_ids = self.env['product.product'].search([('id', 'in', product_ids.ids)])
            product_data = []
            for product_id in product_ids:
                value = {}
                counter = 1
                col = "col_"
                if product_id.product_template_attribute_value_ids:
                    variant = product_id.product_template_attribute_value_ids._get_combination_name()
                    name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
                    product_name = name
                else:
                    product_name = product_id.name
                value.update({
                    'product_id': product_id.id,
                    'product_name': product_name or '',
                    'product_code': product_id.default_code or '',
                    'cost_price': product_id.standard_price or 0.00,
                })
                is_last = False
                for date_data in self._get_date_data(data):
                    if counter == 6:
                        is_last = True
                    start_date = date_data.get('start_date')
                    end_date = date_data.get('end_date')
                    company_id = company.id
                    location_id = location.id
                    delivered_qty = self._get_product_location_info(product_id.id, start_date, end_date, is_last,
                                                                    location_id, company_id)
                    received_qty = self._get_product_location_in_info(product_id.id, start_date, end_date, is_last,
                                                                      location_id, company_id)
                    return_in_qty = self._get_return_location_in_qty(product_id.id, start_date, end_date, is_last,
                                                                     location_id, company_id)
                    return_out_qty = self._get_return_location_out_qty(product_id.id, start_date, end_date, is_last,
                                                                       location_id, company_id)
                    adjusted_qty = self._get_adjusted_location_qty(product_id.id, start_date, end_date, is_last,
                                                                   location_id, company_id)
                    qty_on_hand = (received_qty + adjusted_qty + return_in_qty) - (delivered_qty - return_out_qty)
                    qty_hand_key = col + str(counter)
                    value.update({qty_hand_key: qty_on_hand})
                    counter += 1
                product_data.append(value)
            lines.append({'product_data': product_data})
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        company_id = self.env['res.company'].browse(data['form']['company_id'][0])
        period_length = data['form']['period_length']
        start_date = data['form']['date_from']
        start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        filter_type = data['form']['filter_type']
        category_ids = self.env['product.category'].browse(data['form']['product_categ_ids'])
        product_ids = self.env['product.product'].browse(data['form']['product_ids'])
        location_ids = self.env['stock.location'].browse(data['form']['location_ids'])
        warehouse_ids = self.env['stock.warehouse'].browse(data['form']['warehouse_ids'])
        date_from = datetime.strptime(data['form']['date_from'], "%Y-%m-%d").strftime("%d-%m-%Y")
        data = {
            'filter_type': filter_type,
            'start_date': start_date,
            'date_from': date_from,
            'warehouse_ids': warehouse_ids,
            'location_ids': location_ids,
            'product_ids': product_ids,
            'category_ids': category_ids,
            'period_length': period_length,
            'company_id': company_id,
            'frequent_stock': data['form'].get('frequent_stock'),
            'less_frequent_stock': data['form'].get('less_frequent_stock'),
            'stuck_up': data['form'].get('stuck_up'),
            'dead': data['form'].get('dead'),
            'branch': data['form'].get('branch'),
        }
        docargs = {
            'doc_model': 'stock.aging.report.wizard',
            'data': data,
            'get_columns': self._get_columns,
            'get_warehouse_details': self._get_warehouse_details,
            'get_location_details': self._get_location_details,
        }
        return docargs
