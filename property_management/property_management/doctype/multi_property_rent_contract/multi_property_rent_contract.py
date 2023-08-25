# -*- coding: utf-8 -*-
# Copyright (c) 2020, shakeel vaim and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, formatdate, today, date_diff, nowdate, get_first_day, flt, cint, get_last_day, add_days,add_months
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.utils import money_in_words
import erpnext

class MultiPropertyRentContract(Document):
	def validate(self):
		total_rent_amount = 0
		property_deposite = self.deposit_amount / len(self.property_details)
		for row in self.property_details:
			row.deposit = property_deposite
			if row.actual_rent and row.discount:
				row.payable_rent_amount = flt(row.actual_rent)-flt(row.actual_rent * row.discount) / 100
				total_rent_amount += row.payable_rent_amount
			else:
				row.payable_rent_amount = flt(row.actual_rent)
				total_rent_amount += row.payable_rent_amount
			row.monthly_payable_amount = flt(row.payable_rent_amount) / flt(self.payment_period)
		self.rent = total_rent_amount

	# def on_submit(self):
	# 	self.process_invoice()

	def process_invoice(self):
		period_start_in_middle_of_month = period_end_in_middle_of_month = False
		if not getdate(get_first_day(self.contract_start_date)) == getdate(self.contract_start_date):
			period_start_in_middle_of_month = True
		if not getdate(get_last_day(self.contract_start_date)) == getdate(self.contract_end_date):
			period_end_in_middle_of_month = True
		contract_start_date = self.contract_start_date
		invoice_count = 0
		while getdate(contract_start_date) < getdate(self.contract_end_date):
			period_start_date = getdate(contract_start_date)
			if period_start_in_middle_of_month == True and self.payment_date_calculation == "Month Start Date":
				period_end_date = getdate(get_last_day(period_start_date))
			else:	
				period_end_date = add_days(add_months(getdate(period_start_date),cint(self.payment_period)),-1)
			if period_start_in_middle_of_month == True and self.payment_date_calculation == "Month Start Date":
				items = []
				for mc_row in self.property_details:
					rent = get_rent(period_start_date,period_end_date,mc_row.monthly_payable_amount)
					item = get_items_from_contract(mc_row,rent)
					items.append(item)
				create_invoice(self.name,period_start_date,period_start_date,period_end_date,items)
				# period_start_in_middle_of_month = False
				invoice_count += 1
			elif getdate(period_end_date) >= getdate(self.contract_end_date):
				if period_end_in_middle_of_month == True:
					if getdate(period_end_date) > getdate(self.contract_end_date):
						items = []
						for mc_row in self.property_details:
							rent = get_rent(period_start_date,self.contract_end_date,mc_row.monthly_payable_amount)
							item = get_items_from_contract(mc_row,rent)
							items.append(item)
						# rent = get_rent(period_start_date,self.contract_end_date,self.monthly_payable_amount)
						create_invoice(self.name,period_start_date,period_start_date,self.contract_end_date,items)
						period_end_in_middle_of_month = False
						invoice_count += 1
					else:
						items = []
						for mc_row in self.property_details:
							rent = flt(mc_row.payable_rent_amount)
							item = get_items_from_contract(mc_row,rent)
							items.append(item)
						create_invoice(self.name,period_start_date,period_start_date,period_end_date,items)
						invoice_count += 1
			else:
				# rent = flt(self.final_rent_amount)
				items = []
				for mc_row in self.property_details:
					rent = flt(mc_row.payable_rent_amount)
					item = get_items_from_contract(mc_row,rent)
					items.append(item)
				create_invoice(self.name,period_start_date,period_start_date,period_end_date,items)
				invoice_count += 1
			if period_start_in_middle_of_month == True and self.payment_date_calculation == "Month Start Date":
				contract_start_date = add_days(period_end_date,1)
				period_start_in_middle_of_month = False
			else:
				contract_start_date = add_months(period_start_date,cint(self.payment_period))

		frappe.msgprint(_("{0} Invoice Created Successfully").format(invoice_count))
		frappe.db.set_value("Multi Property Rent Contract",self.name,"invoice_created",1)

	def process_deposite_invoice(self):
		items = self.get_deposite_invoice_item()
		create_owner_invoice(self.tenant,self.contract_start_date,self.contract_start_date,self.contract_end_date,self.name,items)

	def get_deposite_invoice_item(self):
		items = []
		property_setting = frappe.get_doc("Property Setting","Property Setting")
		if not property_setting.insurance_item:
			frappe.throw(_("Please Select Insurance Item In Property Management Setting"))
		else:
			item_code = property_setting.insurance_item
			item_dict = dict(
				item_code = item_code,
				qty = 1,
				rate = self.deposit_amount
			)
			items.append(item_dict)
		return items


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

def get_rent(start_date,end_date,rent):
	rent_day = 	date_diff(end_date,start_date)
	rent_per_day = flt(rent) / flt(30)
	rent = rent_day * rent_per_day
	return rent


@frappe.whitelist()
def create_invoice(contract,date,start_date,end_date,items):
	contract_data = frappe.get_doc("Multi Property Rent Contract",contract)
	# items = []
	# item = get_items_from_contract(contract_data,rent)
	# items.append(item)
	sales_invoice_doc = frappe.get_doc(dict(
		doctype = "Sales Invoice",
		customer = contract_data.tenant,
		posting_date = date,
		period_start_date = getdate(start_date),
		period_end_date = getdate(end_date),
		contract_no = contract_data.name,
		set_posting_time = 1,
		items = items,
		is_property_invoice = 1,
		is_multi_contract_invoice = 1
	)).insert(ignore_permissions = True)
	sales_invoice_doc.submit()

def get_items_from_contract(contract_data,rent):
	income_account = frappe.db.get_value("Property",contract_data.property,"revenue_account")
	item = frappe.db.get_value("Property Setting","Property Setting","invoice_item")
	rate = rent
	item  = dict(
		item_code = item,
		qty = 1,
		rate = rate,
		income_account = income_account,
		property = contract_data.property,
		building = contract_data.building,
		contract_no = contract_data.parent
	)
	return item

def create_owner_invoice(customer,date,from_date,to_date,contract_no,items):
    doc = frappe.get_doc(dict(
		doctype = "Sales Invoice",
		customer = customer,
		posting_date = getdate(from_date),
		period_start_date = getdate(from_date),
		period_end_date = getdate(to_date),
		contract_no = contract_no,
		set_posting_time = 1,
		items = items,
		is_property_invoice = 1,
        is_deposite_invoice = 1,
        is_multi_contract_invoice = 1
    )).insert(ignore_permissions = True)
