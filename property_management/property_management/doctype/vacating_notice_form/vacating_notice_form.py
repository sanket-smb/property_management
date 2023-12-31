# -*- coding: utf-8 -*-
# Copyright (c) 2020, shakeel vaim and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class VacatingNoticeForm(Document):
	def on_submit(self):
		frappe.msgprint('call')
		cancel_remain_invoice(self.contract,self.check_out_date)
		delete_remain_invoice(self.contract,self.check_out_date)
		rent_doc = frappe.get_doc("Rent Contract",self.contract)
		rent_doc.contract_end_date = self.check_out_date
		rent_doc.save()

@frappe.whitelist()
def cancel_remain_invoice(contract,date):
	filters = [
		["Sales Invoice","contract_no","=",contract],
		["Sales Invoice","period_start_date",">",date],
		["Sales Invoice","docstatus","in",["1"]]
	]
	invoices = frappe.get_all("Sales Invoice",filters=filters,fields=["name"])
	for inv in invoices:
		invoice_doc = frappe.get_doc("Sales Invoice",inv.name)
		invoice_doc.cancel()

@frappe.whitelist()
def delete_remain_invoice(contract,date):
	filters = [
		["Sales Invoice","contract_no","=",contract],
		["Sales Invoice","period_start_date",">",date],
		["Sales Invoice","docstatus","in",["0"]]
	]
	invoices = frappe.get_all("Sales Invoice",filters=filters,fields=["name"])
	for invc in invoices:
		invoice_doc = frappe.get_doc("Sales Invoice",invc.name)
		invoice_doc.delete()


@frappe.whitelist()
def make_inspection(source_name, target_doc=None):
	doclist = get_mapped_doc("Vacating Notice Form", source_name, {
			"Vacating Notice Form": {
				"doctype": "Property Inspection",
				"validation": {
					"docstatus": ["=", 1]
				},
				"field_map": {
					"vacating_notice_form": "name",
					"check_out_date" :"actual_check_out_date"
				}
			}
		})

	# postprocess: fetch shipping address, set missing values

	return doclist
