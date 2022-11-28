# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_round

import logging

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Cannot `import xlsxwriter`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class StockAgingReportWizard(models.TransientModel):
    _name = 'stock.aging.report.wizard'
    _description = 'Stock Aging Report'

    date_from = fields.Date('Start Date')
    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouse")
    location_ids = fields.Many2many('stock.location', string="Location")
    product_ids = fields.Many2many('product.product', string="Product")
    product_categ_ids = fields.Many2many('product.category', string="Category")
    filter_type = fields.Selection([('product', 'Product'), ('category', 'Category')], default='product',
                                   string='Filter By')
    document = fields.Binary('File To Download')
    file = fields.Char('Report File Name', readonly=1)
    period_length = fields.Integer('Period Length (Days)', default=30)
    company_id = fields.Many2one('res.company', 'Company')
    report_type = fields.Selection([('warehouse', 'Warehouse'), ('location', 'Location')], default='warehouse',
                                   string='Generate Report Based on')
    frequent_stock = fields.Char("Frequent Stock")
    less_frequent_stock = fields.Char("Less Frequent stock")
    stuck_up = fields.Char("Stuck Up")
    dead = fields.Char("Dead")
    branch = fields.Char("Branch")

    @api.onchange('filter_type')
    def _onchange_filter_type(self):
        if self.filter_type == 'product':
            self.product_categ_ids = False
        else:
            self.product_ids = False

    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type == 'warehouse':
            self.location_ids = False
        else:
            self.warehouse_ids = False

    def print_pdf_report(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
            'ids': [1],
            'model': 'stock.aging.report.wizard',
            'form': data
        }
        return self.env.ref('stock_ageing_report_app.action_report_stock_aging').report_action(self, data=datas)

    def get_columns(self, data):
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

    # Warehouse

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

    def get_warehouse_details(self, data, warehouse):
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

    def get_location_details(self, data, location):
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

    def print_excel_report(self):
        self.ensure_one()
        [data] = self.read()
        file_path = 'Stock Aging Report' + '.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + file_path)
        worksheet = workbook.add_worksheet('Stock Aging Report')

        header_format = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'font_size': 16, 'align': 'center', 'bg_color': '#D8D8D8'})
        title_format = workbook.add_format(
            {'border': 1, 'bold': True, 'valign': 'vcenter', 'align': 'center', 'font_size': 14, 'bg_color': '#D8D8D8'})
        cell_wrap_format = workbook.add_format(
            {'border': 1, 'valign': 'vjustify', 'valign': 'vcenter', 'align': 'left', 'font_size': 12, })  ##E6E6E6
        cell_wrap_format_right = workbook.add_format(
            {'border': 1, 'valign': 'vjustify', 'valign': 'vcenter', 'align': 'right', 'font_size': 12, })  ##E6E6E6
        cell_wrap_format_val = workbook.add_format(
            {'border': 1, 'valign': 'vjustify', 'valign': 'vcenter', 'align': 'right', 'font_size': 12, })  ##E6E6E6
        cell_wrap_format_val.set_font_color('#006600')
        cell_wrap_format_bold = workbook.add_format(
            {'border': 1, 'bold': True, 'valign': 'vjustify', 'valign': 'vcenter', 'align': 'center', 'font_size': 12,
             'bg_color': '#D8D8D8'})  ##E6E6E6
        cell_wrap_format_amount = workbook.add_format(
            {'border': 1, 'valign': 'vjustify', 'valign': 'vcenter', 'align': 'right', 'font_size': 12,
             'bold': True})  ##E6E6E6
        cell_wrap_format_amount_val = workbook.add_format(
            {'border': 1, 'valign': 'vjustify', 'valign': 'vcenter', 'align': 'right', 'font_size': 12,
             'bold': True})  ##E6E6E6
        cell_wrap_format_amount.set_font_color('#006600')

        worksheet.set_row(1, 20)  # Set row height
        # Merge Row Columns
        TITLEHEDER = 'Stock Aging Report'
        worksheet.set_column(0, 15, 20)

        ware_obj = self.env['stock.warehouse']
        location_obj = self.env['stock.location']

        period_length = data.get('period_length')
        start_date = data.get('date_from')
        start_date = datetime.strptime(str(start_date), "%Y-%m-%d").strftime("%Y-%m-%d")
        filter_type = data.get('filter_type')
        category_ids = self.env['product.category'].browse(data.get('product_categ_ids'))
        product_ids = self.env['product.product'].browse(data.get('product_ids'))
        location_ids = self.env['stock.location'].browse(data.get('location_ids'))
        warehouse_ids = self.env['stock.warehouse'].browse(data.get('warehouse_ids'))
        date_from = datetime.strptime(str(data.get('date_from')), "%Y-%m-%d").strftime("%d-%m-%Y")
        company_id = self.env['res.company'].browse(data.get('company_id')[0])
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
            'frequent_stock': self.frequent_stock,
            'less_frequent_stock': self.less_frequent_stock,
            'stuck_up': self.stuck_up,
            'dead': self.dead,
            'branch': self.branch,
        }

        worksheet.merge_range(1, 0, 1, 15, TITLEHEDER, header_format)
        rowscol = 1
        if warehouse_ids:
            for warehouse in warehouse_ids:
                # Report Title
                worksheet.merge_range((rowscol + 2), 0, (rowscol + 2), 3, 'Warehouse/Location', title_format)
                worksheet.merge_range((rowscol + 2), 12, (rowscol + 2), 15, str(warehouse.name), title_format)

                worksheet.merge_range((rowscol + 4), 0, (rowscol + 4), 3, 'Company: ', title_format)
                worksheet.merge_range((rowscol + 5), 0, (rowscol + 5), 3, str(company_id.name), title_format)

                worksheet.merge_range((rowscol + 4), 6, (rowscol + 4), 9, 'Start Date: ', title_format)
                worksheet.merge_range((rowscol + 5), 6, (rowscol + 5), 9, str(start_date), title_format)

                worksheet.merge_range((rowscol + 4), 12, (rowscol + 4), 15, 'Period Length:', title_format)
                worksheet.merge_range((rowscol + 5), 12, (rowscol + 5), 15, str(period_length), title_format)

                rowscol += 5

                worksheet.merge_range((rowscol + 4), 0, (rowscol + 4), 3, 'Frequent Stock: ', title_format)
                worksheet.merge_range((rowscol + 5), 0, (rowscol + 5), 3,
                                      data.get('frequent_stock') if data.get('frequent_stock') else '-', title_format)

                worksheet.merge_range((rowscol + 4), 6, (rowscol + 4), 9, 'Less Frequent stock: ', title_format)
                worksheet.merge_range((rowscol + 5), 6, (rowscol + 5), 9,
                                      data.get('less_frequent_stock') if data.get('less_frequent_stock') else '-',
                                      title_format)

                worksheet.merge_range((rowscol + 4), 12, (rowscol + 4), 15, 'Stuck Up:', title_format)
                worksheet.merge_range((rowscol + 5), 12, (rowscol + 5), 15,
                                      data.get('stuck_up') if data.get('stuck_up') else '-', title_format)

                rowscol += 4

                worksheet.merge_range((rowscol + 4), 0, (rowscol + 4), 3, 'Dead:: ', title_format)
                worksheet.merge_range((rowscol + 5), 0, (rowscol + 5), 3, data.get('dead') if data.get('dead') else '-',
                                      title_format)

                worksheet.merge_range((rowscol + 4), 6, (rowscol + 4), 9, 'Branch: ', title_format)
                worksheet.merge_range((rowscol + 5), 6, (rowscol + 5), 9,
                                      data.get('branch') if data.get('branch') else '-', title_format)

                # Report Content
                worksheet.write((rowscol + 7), 0, 'Code', cell_wrap_format_bold)
                worksheet.write((rowscol + 7), 1, 'Product Name', cell_wrap_format_bold)
                worksheet.write((rowscol + 7), 2, 'Total Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 7), 3, 'Total Value', cell_wrap_format_bold)
                col = 4
                for value in self.get_columns(data):
                    colss = col + 1
                    worksheet.merge_range((rowscol + 7), col, (rowscol + 7), colss, str(value), title_format)
                    col += 2
                worksheet.write((rowscol + 8), 0, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 1, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 2, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 3, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 4, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 5, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 6, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 7, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 8, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 9, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 10, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 11, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 12, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 13, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 14, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 15, 'Value', cell_wrap_format_bold)
                rows = (rowscol + 9)
                for records in self.get_warehouse_details(data, warehouse):
                    for record in records.get('product_data'):
                        col_1_data = record.get('col_1')
                        col_1_data_value = col_1_data * record.get('cost_price')
                        col_2_data = record.get('col_2')
                        col_2_data_value = col_2_data * record.get('cost_price')
                        col_3_data = record.get('col_3')
                        col_3_data_value = col_3_data * record.get('cost_price')
                        col_4_data = record.get('col_4')
                        col_4_data_value = col_4_data * record.get('cost_price')
                        col_5_data = record.get('col_5')
                        col_5_data_value = col_5_data * record.get('cost_price')
                        col_6_data = record.get('col_6')
                        col_6_data_value = col_6_data * record.get('cost_price')

                        sub_total = col_1_data + col_2_data + col_3_data + col_4_data + col_5_data + col_6_data

                        total_cost = sub_total * record.get('cost_price')

                        worksheet.write(rows, 0, record.get('product_code'), cell_wrap_format)
                        worksheet.write(rows, 1, record.get('product_name'), cell_wrap_format)

                        worksheet.write(rows, 2, str('%.2f' % sub_total), cell_wrap_format_val)
                        worksheet.write(rows, 3, str('%.2f' % total_cost), cell_wrap_format_right)

                        worksheet.write(rows, 4, str('%.1f' % col_1_data), cell_wrap_format_amount)
                        worksheet.write(rows, 5, str('%.2f' % col_1_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 6, str('%.1f' % col_2_data), cell_wrap_format_amount)
                        worksheet.write(rows, 7, str('%.2f' % col_2_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 8, str('%.1f' % col_3_data), cell_wrap_format_amount)
                        worksheet.write(rows, 9, str('%.2f' % col_3_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 10, str('%.1f' % col_4_data), cell_wrap_format_amount)
                        worksheet.write(rows, 11, str('%.2f' % col_4_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 12, str('%.1f' % col_5_data), cell_wrap_format_amount)
                        worksheet.write(rows, 13, str('%.2f' % col_5_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 14, str('%.1f' % col_6_data), cell_wrap_format_amount)
                        worksheet.write(rows, 15, str('%.2f' % col_6_data_value), cell_wrap_format_amount_val)
                        rows = rows + 1
                    rows = rows
                rowscol = rows + 2
        else:
            for location in location_ids:
                if location.location_id:
                    location_name = str(location.location_id.name or '') + '/' + str(location.name or '')
                else:
                    location_name = str(location.name or '')
                # Report Title
                worksheet.merge_range((rowscol + 2), 0, (rowscol + 2), 3, 'Warehouse/Location', title_format)
                worksheet.merge_range((rowscol + 2), 12, (rowscol + 2), 15, str(location_name), title_format)

                worksheet.merge_range((rowscol + 4), 0, (rowscol + 4), 3, 'Company: ', title_format)
                worksheet.merge_range((rowscol + 5), 0, (rowscol + 5), 3, str(company_id.name), title_format)

                worksheet.merge_range((rowscol + 4), 6, (rowscol + 4), 9, 'Start Date: ', title_format)
                worksheet.merge_range((rowscol + 5), 6, (rowscol + 5), 9, str(start_date), title_format)

                worksheet.merge_range((rowscol + 4), 12, (rowscol + 4), 15, 'Period Length:', title_format)
                worksheet.merge_range((rowscol + 5), 12, (rowscol + 5), 15, str(period_length), title_format)

                # Report Content
                worksheet.write((rowscol + 7), 0, 'Code', cell_wrap_format_bold)
                worksheet.write((rowscol + 7), 1, 'Product Name', cell_wrap_format_bold)
                worksheet.write((rowscol + 7), 2, 'Total Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 7), 3, 'Total Value', cell_wrap_format_bold)
                col = 4
                for value in self.get_columns(data):
                    colss = col + 1
                    worksheet.merge_range((rowscol + 7), col, (rowscol + 7), colss, str(value), title_format)
                    col += 2
                worksheet.write((rowscol + 8), 0, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 1, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 2, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 3, '', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 4, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 5, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 6, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 7, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 8, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 9, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 10, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 11, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 12, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 13, 'Value', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 14, 'Qty', cell_wrap_format_bold)
                worksheet.write((rowscol + 8), 15, 'Value', cell_wrap_format_bold)
                rows = (rowscol + 9)
                for records in self.get_location_details(data, location):
                    for record in records.get('product_data'):
                        col_1_data = record.get('col_1')
                        col_1_data_value = col_1_data * record.get('cost_price')
                        col_2_data = record.get('col_2')
                        col_2_data_value = col_2_data * record.get('cost_price')
                        col_3_data = record.get('col_3')
                        col_3_data_value = col_3_data * record.get('cost_price')
                        col_4_data = record.get('col_4')
                        col_4_data_value = col_4_data * record.get('cost_price')
                        col_5_data = record.get('col_5')
                        col_5_data_value = col_5_data * record.get('cost_price')
                        col_6_data = record.get('col_6')
                        col_6_data_value = col_6_data * record.get('cost_price')

                        sub_total = col_1_data + col_2_data + col_3_data + col_4_data + col_5_data + col_6_data

                        total_cost = sub_total * record.get('cost_price')

                        worksheet.write(rows, 0, record.get('product_code'), cell_wrap_format)
                        worksheet.write(rows, 1, record.get('product_name'), cell_wrap_format)

                        worksheet.write(rows, 2, str('%.2f' % sub_total), cell_wrap_format_val)
                        worksheet.write(rows, 3, str('%.2f' % total_cost), cell_wrap_format_right)

                        worksheet.write(rows, 4, str('%.1f' % col_1_data), cell_wrap_format_amount)
                        worksheet.write(rows, 5, str('%.2f' % col_1_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 6, str('%.1f' % col_2_data), cell_wrap_format_amount)
                        worksheet.write(rows, 7, str('%.2f' % col_2_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 8, str('%.1f' % col_3_data), cell_wrap_format_amount)
                        worksheet.write(rows, 9, str('%.2f' % col_3_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 10, str('%.1f' % col_4_data), cell_wrap_format_amount)
                        worksheet.write(rows, 11, str('%.2f' % col_4_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 12, str('%.1f' % col_5_data), cell_wrap_format_amount)
                        worksheet.write(rows, 13, str('%.2f' % col_5_data_value), cell_wrap_format_amount_val)
                        worksheet.write(rows, 14, str('%.1f' % col_6_data), cell_wrap_format_amount)
                        worksheet.write(rows, 15, str('%.2f' % col_6_data_value), cell_wrap_format_amount_val)
                        rows = rows + 1
                    rows = rows
                rowscol = rows + 2
        workbook.close()
        buf = base64.b64encode(open('/tmp/' + file_path, 'rb+').read())
        self.document = buf
        self.file = 'Stock Aging Report' + '.xlsx'
        return {
            'res_id': self.id,
            'name': 'Files to Download',
            'view_type': 'form',
            "view_mode": 'form,tree',
            'res_model': 'stock.aging.report.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
