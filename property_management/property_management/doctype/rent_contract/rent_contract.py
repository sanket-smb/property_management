
# -*- coding: utf-8 -*-
# Copyright (c) 2015, shakeel vaim and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, formatdate, today, date_diff, nowdate, get_first_day, flt, cint, get_last_day, add_days,add_months
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.utils import money_in_words
import erpnext
from property_management.api import create_owner_invoice
import pandas as pd
from datetime import timedelta,datetime,date
import calendar
from frappe.utils.data import add_to_date

class RentContract(Document):
	def autoname(self):
		if(self.extended_from and self.extension_count):
			self.name = self.extended_from +"R-"+ str(self.extension_count)

#	def autoname(self):
#		self.name = make_autoname(self.property + '-RC.###')

	def validate(self):
		if self.monthly_payable_amount and self.payment_period:
			self.final_rent_amount = flt(self.monthly_payable_amount) * flt(self.payment_period)
			self.rent = self.final_rent_amount
		elif self.final_rent_amount and self.payment_period:
			self.monthly_payable_amount = flt(self.final_rent_amount) / flt(self.payment_period)
		self.final_rent_amount = self.rent - self.discount
		self.deposit_amount_in_words = money_in_words(self.deposit_amount)
		self.rent_amount_in_words = money_in_words(self.rent)
		self.final_rent_amount_in_words = money_in_words(self.final_rent_amount)
		if date_diff(self.contract_end_date, self.contract_start_date) < 0:
			frappe.throw(_("Rent Start Date cannot be before Rent End Date"))
		rent_contracts = frappe.db.sql("""select r.name as contract,r.contract_start_date as sd,r.contract_end_date as ed,v.name as vnf from `tabRent Contract` as r left join 
				`tabVacating Notice Form` as v on r.name = v.contract where v.docstatus = 1 and r.name != %s and r.docstatus != 2 and r.property=%s """,(self.name,self.property),as_dict=1)
		if rent_contracts:
			for i in rent_contracts:
				if "vnf" in i and i["vnf"]:
					start_date = i["sd"]
					new_end_date = frappe.db.get_value("Vacating Notice Form",i["vnf"],"check_out_date")
					#frappe.errprint(start_date)
					#frappe.errprint(self.contract_start_date)
					#frappe.errprint(new_end_date)
					#frappe.errprint(self.contract_end_date)
					if (start_date <= getdate(self.contract_start_date) and new_end_date >= getdate(self.contract_end_date)) or (start_date >= getdate(self.contract_start_date) and  start_date <= getdate(self.contract_end_date)) or (new_end_date >= getdate(self.contract_start_date) and new_end_date <= getdate(self.contract_end_date)):
						frappe.throw(_("Rent Contract '{0}' with Contract Start Date '{1}' Contract End Date '{2}' Overlap with this contract for property '{3}'".format(i['contract'],formatdate(i['sd']),formatdate(i['ed']),self.property)))
				else:
					if frappe.db.sql("""select name from `tabRent Contract` where docstatus != {0}  and (( contract_start_date<='{1}' and contract_end_date>='{2}' ) 
						or ( contract_start_date>='{1}' and contract_start_date<='{2}') or  (contract_end_date>='{1}' and contract_end_date<='{2}' )) and name = '{3}' 
						""".format(2,self.contract_start_date,self.contract_end_date,i['contract'])):
						frappe.throw(_("Rent Contract '{0}' with Contract Start Date '{1}' Contract End Date '{2}' Overlap with this contract for property '{3}'".format(i['contract'],formatdate(i['sd']),formatdate(i['ed']),self.property)))


#		exist=frappe.db.sql("""select name,contract_start_date,contract_end_date from `tabRent Contract` where name !='%s' and docstatus != 2 and property='%s' and 
#				(( contract_start_date<='%s' and contract_end_date>='%s') or ( contract_start_date>='%s' and contract_start_date<='%s') or
#				( contract_end_date>='%s' and contract_end_date<='%s'))
#			"""%(self.name,self.property,self.contract_start_date,self.contract_end_date,self.contract_start_date,self.contract_end_date,self.contract_start_date,self.contract_end_date))
#		for i in exist:
#			if frappe.db.exists("Vacating Notice Form",{"contract":i[0]}):
#				doc = frappe.get_doc("Vacating Notice Form",{"contract":i[0]})
#				if doc:
#					new_end_date = doc.check_out_date
#					if frappe.db.sql("""select name,contract_start_date,contract_end_date from `tabRent Contract` where name !='%s' and docstatus != 2 and property='%s' and 
#                               		(( contract_start_date<='%s' and contract_end_date>='%s') or ( contract_start_date>='%s' and contract_start_date<='%s') or
#                             		( contract_end_date>='%s' and contract_end_date<='%s'))
#                       			"""%(self.name,self.property,self.contract_start_date,new_end_date,self.contract_start_date,new_end_date,self.contract_start_date,new_end_date))
#						frappe.throw(_("Rent Contract '{0}' with Contract Start Date '{1}' Contract End Date '{2}' Overlap with this contract for property '{3}'".format(i[0],formatdate(i[1]),formatdate(i[2]),self.property)))
#				else:
#					frappe.throw(_("Rent Contract '{0}' with Contract Start Date '{1}' Contract End Date '{2}' Overlap with this contract for property '{3}'".format(i[0],formatdate(i[1]),formatdate(i[2]),self.property)))
#			else:
#				frappe.throw(_("Rent Contract '{0}' with Contract Start Date '{1}' Contract End Date '{2}' Overlap with this contract for property '{3}'".format(i[0],formatdate(i[1]),formatdate(i[2]),self.property)))

	def on_submit(self):
		if getdate(self.contract_start_date)<=getdate(today()) and getdate(self.contract_end_date)>=getdate(today()):
			frappe.db.set_value('Property',self.property,'status','Rented')

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
				rent = get_rent(period_start_date,period_end_date,self.monthly_payable_amount)
				create_invoice(self.name,period_start_date,period_start_date,period_end_date,rent)
				# period_start_in_middle_of_month = False
				invoice_count += 1
			elif getdate(period_end_date) >= getdate(self.contract_end_date):
				if period_end_in_middle_of_month == True:
					if getdate(period_end_date) > getdate(self.contract_end_date):
						rent = get_rent(period_start_date,self.contract_end_date,self.monthly_payable_amount)
						create_invoice(self.name,period_start_date,period_start_date,self.contract_end_date,rent)
						period_end_in_middle_of_month = False
						invoice_count += 1
					else:
						rent = flt(self.final_rent_amount)
						create_invoice(self.name,period_start_date,period_start_date,period_end_date,rent)
						invoice_count += 1
				else:
					rent = flt(self.final_rent_amount)
					create_invoice(self.name,period_start_date,period_start_date,period_end_date,rent)
					invoice_count += 1
			else:
				rent = flt(self.final_rent_amount)
				create_invoice(self.name,period_start_date,period_start_date,period_end_date,rent)
				invoice_count += 1
			if period_start_in_middle_of_month == True and self.payment_date_calculation == "Month Start Date":
				contract_start_date = add_days(period_end_date,1)
				period_start_in_middle_of_month = False
			else:
				contract_start_date = add_months(period_start_date,cint(self.payment_period))

		frappe.msgprint(_("{0} Invoice Created Successfully").format(invoice_count))
		frappe.db.set_value("Rent Contract",self.name,"invoice_created",1)

	def process_deposite_invoice(self):
		items = self.get_deposite_invoice_item()
		create_owner_invoice(self.tenant,self.contract_start_date,self.contract_start_date,self.contract_end_date,self.name,self.property,self.building,items)

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

def get_rent(start_date,end_date,rent):
	rent_day = date_diff(end_date,start_date) + 1
	last_day_of_month = get_last_day(start_date).day
	rent_per_day = flt(rent) / flt(last_day_of_month)
	rent = rent_day * rent_per_day
	rent = round(rent)
	return rent

def update_status():
	rented=frappe.db.sql("select rc.property as property from `tabRent Contract` rc, tabProperty p where rc.property=p.name and p.status<>'Rented' and rc.contract_start_date=CURDATE()",as_dict=True)
	for record in rented:
		frappe.db.set_value('Property',record.get('property'),'status','Rented')

	available=frappe.db.sql("select rc.property as property from `tabRent Contract` rc, tabProperty p where rc.property=p.name and p.status='Rented' and rc.contract_end_date=date_add(CURDATE(),interval -1 day)",as_dict=True)
	for record in rented:
		frappe.db.set_value('Property',record.get('property'),'status','Available')


@frappe.whitelist()
def cancel_contract(rent_contract):
	frappe.db.set_value('Rent Contract',rent_contract,'contract_end_date',nowdate())
	return "Rent Contract '{0}' have Cancled Today. Contract End Date is '{1}'".format(rent_contract,formatdate(nowdate()))


@frappe.whitelist()
def create_invoice(contract,date,start_date,end_date,rent):
	contract_data = frappe.get_doc("Rent Contract",contract)
	items = []
	item = get_items_from_contract(contract_data,rent)
	items.append(item)
	sales_invoice_doc = frappe.get_doc(dict(
		doctype = "Sales Invoice",
		customer = contract_data.tenant,
		posting_date = date,
		period_start_date = getdate(start_date),
		period_end_date = getdate(end_date),
		property = contract_data.property,
		building = contract_data.building,
		contract_no = contract_data.name,
		invoice_type_format = contract_data.invoice_type_format,
		set_posting_time = 1,
		items = items,
		is_property_invoice = 1
	))
	sales_invoice_doc.save(ignore_permissions = True)
	#sales_invoice_doc.submit()

def get_items_from_contract(contract_data,rent):
	income_account = frappe.db.get_value("Property",contract_data.property,"revenue_account")
	item = ""
	if(int(contract_data.payment_period) > 1):
		item = frappe.db.get_value("Property Setting","Property Setting","accrued_rent_item")
	else:
		item = frappe.db.get_value("Property Setting","Property Setting","invoice_item")
	rate = rent
	item  = dict(
		item_code = item,
		qty = 1,
		rate = rate,
		income_account = income_account,
		property = contract_data.property,
		building = contract_data.building,
		contract_no = contract_data.name,
	)
	return item

@frappe.whitelist(allow_guest=True)
def extend(doc_name,no_of_months):
	doc = frappe.get_doc("Rent Contract",doc_name)
	new_doc = frappe.copy_doc(doc)
	end_date = new_doc.contract_end_date
	new_doc.contract_start_date = end_date + timedelta(days = 1)
	new_doc.invoice_created = 0

	ced = add_to_date(new_doc.contract_start_date ,months = int(no_of_months)) # - timedelta(days = 1)
	new_doc.contract_end_date = add_to_date(ced ,days = -1)

	extended_from = doc.name
	extension_count = 0

	if hasattr(doc, "extended_from"):
		if doc.extended_from:
			extended_from = doc.extended_from
	extension_count = frappe.db.sql(""" select max(extension_count) from `tabRent Contract` where extended_from = %s """,extended_from)[0][0]
	if not extension_count:
		extension_count = 1
	else:
		extension_count = int(extension_count) + 1
	new_doc.extended_from = extended_from
	new_doc.extension_count = extension_count
	new_doc.date = today()
	new_doc.name = doc.name + 'R'
	new_doc.insert()
	new_doc.save()

	return new_doc.name

