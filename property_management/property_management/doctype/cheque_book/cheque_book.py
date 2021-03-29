# -*- coding: utf-8 -*-
# Copyright (c) 2021, shakeel vaim and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class ChequeBook(Document):
	def before_insert(self):
		self.next_cheque = self.start_number

	def validate(self):
		if self.end_number == self.last_used_cheque:
			self.cheque_finished = 1
