# -*- coding: utf-8 -*-
# Copyright (c) 2020, shakeel vaim and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class MultiPropertyRentContract(Document):
	def validate(self):
		total_rent_amount = 0
		property_deposite = self.deposit_amount / len(self.property_details)
		for row in self.property_details:
			row.deposit = property_deposite
			if row.actual_rent and row.discount:
				row.payable_rent_amount = flt(row.actual_rent)-flt(row.actual_rent * row.discount) / 100
				if row.deposit:
					row.payable_rent_amount -= row.deposit
				total_rent_amount += row.payable_rent_amount
			else:
				row.payable_rent_amount = flt(row.actual_rent)
				if row.deposit:
					row.payable_rent_amount -= row.deposit
				total_rent_amount += row.payable_rent_amount		
		self.rent = total_rent_amount

	def on_submit(self):
		create_rent_contract(self)


def create_rent_contract(self):
	for row in self.property_details:
		property_details = frappe.get_doc("Property",row.property)
		doc = frappe.get_doc(dict(
			doctype = "Rent Contract",
			building = row.building,
			property = row.property,
			property_type = property_details.get("property_type"),
			block_number = property_details.get("block_number"),
			street_name_number = property_details.get("street_name_number"),
			area = property_details.get("area"),
			complex = property_details.get("complex"),
			apt_no = property_details.get("apt_no"),
			ref_no = property_details.get("ref_no"),
			tenant = self.tenant,
			tenant_name = self.tenant_name,
			civil_id = self.civil_id,
			occupation = self.occupation,
			mobile_number = self.mobile_number,
			accomodation_type = self.accomodation_type,
			date = self.date,
			contract_start_date = self.contract_start_date,
			contract_end_date = self.contract_end_date,
			inspection_date = self.inspection_date,
			deposit_amount = row.deposit,
			payment_period = self.payment_period,
			notice_period = self.notice_period,
			rent = row.actual_rent,
			discount = row.discount,
			final_rent_amount = row.payable_rent_amount,
			multi_rent_contract_no = self.name
		)).insert(ignore_permissions = True)


