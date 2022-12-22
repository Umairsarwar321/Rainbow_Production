# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CheckBookSequence(models.Model):
	_name = 'check.book.sequence'
	_rec_name = 'name'
	_description = "Check Book Sequence"

	name = fields.Char('Check Number')
	is_consumed = fields.Boolean("Is Consumed", default=False)
	journal_id = fields.Many2one('account.journal', 'Journal')

	@api.constrains('name')
	def _check_name_unique(self):
		seq_counts = self.search_count([('name', '=', self.name), ('id', '!=', self.id)])
		if seq_counts > 0:
			# raise ValidationError("Check Book Sequence: %s already exists!", ())
			raise ValidationError(_("Check Book Sequence: %s already exists!"
								) % (self.name))

class AccJournalExt(models.Model):
	_inherit = 'account.journal'

	total_cheques = fields.Integer("Total Cheques")
	is_check_created = fields.Boolean("Cheques Created", default=False)

	def write(self, vals):
		rec = super(AccJournalExt, self).write(vals)
		self.create_cheques()
		return rec

	def create_cheques(self):
	# if not self.is_check_created:
		start_check_no = self.check_next_number
		for index in range(self.total_cheques):
			check_num = self.env['check.book.sequence'].search_count([('name', '=', start_check_no), ('journal_id', '=', self.id)])
			if check_num <= 0:

				new_cheque = self.env['check.book.sequence'].sudo().create({
					'name': start_check_no,
					'journal_id': self.id,
				})

			start_check_no = int(start_check_no)
			start_check_no += 1
			start_check_no = str(start_check_no)
			remaining = 5 - len(start_check_no)
			for i in range(remaining):
				start_check_no = '0'+start_check_no
	# else:
	# 	raise ValidationError('Cheques are already created against this journal.')


class AccPaymentCheckExt(models.Model):
	_inherit = 'account.payment'

	check_id = fields.Many2one('check.book.sequence', 'Check Number')

class AccPaymentRegCheckExt(models.TransientModel):
	_inherit = 'account.payment.register'

	check_id = fields.Many2one('check.book.sequence', 'Check No')
	journal_type = fields.Selection([
		('sale', 'Sales'),
		('purchase', 'Purchase'),
		('cash', 'Cash'),
		('bank', 'Bank'),
		('general', 'Miscellaneous'),
	], related='journal_id.type',
		help="Select 'Sale' for customer invoices journals.\n" \
			 "Select 'Purchase' for vendor bills journals.\n" \
			 "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n" \
			 "Select 'General' for miscellaneous operations journals.")

	def action_create_payments(self):
		rec = super(AccPaymentRegCheckExt, self).action_create_payments()
		for line in self.line_ids:
			line.move_id.check_id = self.check_id.id
			self.check_id.is_consumed = True
			payments = self.env['account.payment'].sudo().search([('ref', '=', line.move_id.name)])
			if payments:
				for payment in payments:
					payment.check_id = self.check_id.id
		return rec


class AccMoveCheckExt(models.Model):
	_inherit = 'account.move'

	check_id = fields.Many2one('check.book.sequence', 'Check No')
	# journal_type = fields.Selection([
	# 	('sale', 'Sales'),
	# 	('purchase', 'Purchase'),
	# 	('cash', 'Cash'),
	# 	('bank', 'Bank'),
	# 	('general', 'Miscellaneous'),
	# ],
	# 	help="Select 'Sale' for customer invoices journals.\n" \
	# 		 "Select 'Purchase' for vendor bills journals.\n" \
	# 		 "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n" \
	# 		 "Select 'General' for miscellaneous operations journals.")


class AccPaymentCheckExt(models.Model):
	_inherit = 'account.payment'

	check_id = fields.Many2one('check.book.sequence', 'Check No')
	journal_type = fields.Selection([
		('sale', 'Sales'),
		('purchase', 'Purchase'),
		('cash', 'Cash'),
		('bank', 'Bank'),
		('general', 'Miscellaneous'),
	], related='journal_id.type',
		help="Select 'Sale' for customer invoices journals.\n" \
			 "Select 'Purchase' for vendor bills journals.\n" \
			 "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n" \
			 "Select 'General' for miscellaneous operations journals.")


