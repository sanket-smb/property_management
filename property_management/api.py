from __future__ import unicode_literals
import frappe, erpnext
from frappe.utils import cint, cstr, flt, today,getdate
from frappe import _
from erpnext.accounts.utils import get_children


@frappe.whitelist()
def update_cheque_book(doc,method):
	allowed_cheque = frappe.db.get_value("Mode of Payment",doc.mode_of_payment,"allow_cheque")
	if doc.payment_type == "Pay" and allowed_cheque == "Yes": 
		if doc.reference_no == doc.cheque_no:
			if doc.cheque_book:
				cheque_doc = frappe.get_doc("Cheque Book",doc.cheque_book)
				cheque_doc.last_used_cheque = doc.cheque_no
				cheque_doc.next_cheque = cint(doc.cheque_no) + 1
				cheque_doc.save(ignore_permissions = True)

@frappe.whitelist()
def validate_cheque_no(doc,method):
	allowed_cheque = frappe.db.get_value("Mode of Payment",doc.mode_of_payment,"allow_cheque")
	# frappe.msgprint('out')
	if doc.payment_type == "Pay" and allowed_cheque == "Yes":
		# frappe.msgprint('if')
		validate_duplicate_assignment(doc)
		validate_cheque_no_exists(doc)

def validate_duplicate_assignment(doc):
	filters = [
		["Payment Entry","docstatus","!=","2"],
		["Payment Entry","name","!=",doc.name],
		["Payment Entry","cheque_no","=",doc.cheque_no],
		["Payment Entry","cheque_book","=",doc.cheque_book]
	]
	payment_entry = frappe.get_all("Payment Entry",filters=filters,fields=["name"])
	if payment_entry:
		frappe.throw(_("Cheque book {0}:Cheque No {1} Already Used In Payment Entry {2}").format(doc.cheque_book,doc.cheque_no,payment_entry[0].name))

def validate_cheque_no_exists(doc):
	cheque_book_doc = frappe.get_doc("Cheque Book",doc.cheque_book)
	if int(doc.cheque_no) < int(cheque_book_doc.start_number) or int(doc.cheque_no) > int(cheque_book_doc.end_number):
		frappe.throw(_("Cheque book {0}:Cheque No Must Be Between {1} and {2}").format(doc.cheque_book,cheque_book_doc.start_number,cheque_book_doc.end_number))

@frappe.whitelist()
def account_list():
	from erpnext.accounts.doctype.account.account import update_account_number
	start_number = 1000
	account_data = frappe.db.sql("""select name,is_group,account_name from `tabAccount`""",as_dict=1)
	accounts_done = []
	def check_account(account_list):
		nonlocal start_number
		nonlocal accounts_done                                                                       
		print(start_number)
		for row in account_list:
			if not row.name in accounts_done:
				update_account_number(row.name,row.account_name)
				start_number = start_number + 1
				print(row.name)
				accounts_done.append(row.name)
				if row.is_group == 1:
					accounts = frappe.db.sql("""select name,is_group,account_name from `tabAccount` where parent=%s""",row.name,as_dict=1)
					check_account(accounts)
	check_account(account_data)

@frappe.whitelist()
def get_childer_account_details():
	from erpnext.accounts.doctype.account.account import update_account_number
	start_number = 50001
	accounts_data = get_children('Account','5000 - Source of Funds (Liabilities) - AAA','AAA HOUSING')
	def update_account_number_child(accounts,start_number_loc):
		for row in accounts:
			print(row)
			print(start_number_loc)
			account_name = frappe.db.get_value("Account",row.value,"account_name")
			new_name = update_account_number(row.value,account_name,cstr(start_number_loc))
			account_parent = get_children('Account',new_name,'AAA HOUSING')
			print('-------parent-account---------')
			print(account_parent)
			print('--------end parent-----------')
			if len(account_parent) >= 1:
				up_start_number_loc = cstr(start_number_loc) + cstr(1) 
				update_account_number_child(account_parent,cint(up_start_number_loc))
			if cint(cstr(start_number_loc)[-1]) == 9:
				break
			else:
				start_number_loc += 1
	update_account_number_child(accounts_data,start_number)

@frappe.whitelist()
def account_list_main():
	from erpnext.accounts.doctype.account.account import update_account_number
	start_number = 1000
	account_data = frappe.db.sql("""select name,is_group,account_name from `tabAccount` where is_group=1 and parent_account is null""",as_dict=1)
	for row in account_data:
		update_account_number(row.name,row.account_name,cstr(start_number))
		start_number = start_number + 1000

@frappe.whitelist()
def all_accounts():
	from erpnext.accounts.report.financial_statements import sort_accounts
	accounts = frappe.db.sql("""select name, parent_account,account_name, root_type, report_type, lft, rgt,is_group
	from `tabAccount` order by account_name""",as_dict=True)
	sort_accounts(accounts,True)
	for row in accounts:
		print(row.name)


@frappe.whitelist()
def create_invoice(contract,date,start_date,end_date):
	contract_data = frappe.get_doc("Rent Contract",contract)
	items = get_items_from_contract(contract_data)
	sales_invoice_doc = frappe.get_doc(dict(
		doctype = "Sales Invoice",
		customer = contract_data.tenant,
		posting_date = date,
		period_start_date = start_date,
		period_end_date = end_date,
		property = contract_data.property,
		building = contract_data.building,
		contract_no = contract_data.name,
		items = items
	)).insert(ignore_permissions = True)

def get_items_from_contract(contract_data):
	income_account = frappe.db.get_value("Property",contract_data.property,"revenue_account")
	item = frappe.db.get_value("Property Setting","Property Setting","invoice_item")
	rate = contract_data.rate
	discount = contract_data.discount
	item  = dict(
		item_code = item,
		qty = 1,
		rate = rate,
		discount_amount = discount,
		income_account = income_account,
		property = contract_data.property,
		building = contract_data.building,
		contract_no = contract_data.name
	)
	return item

@frappe.whitelist()
def cancel_remain_invoice(contract,date):
	filters = [
		["Sales Invoice","contract_no","=",contract],
		["Sales Invoice","period_start_date",">",date]
	]
	invoices = frappe.get_all("Sales Invoice",filters=filters,fields=["name"])
	for inv in invoices:
		invoice_doc = frappe.get_doc("Sales Invoice",inv.name)
		invoice_doc.cancel()

@frappe.whitelist()
def create_owner_invoice(customer,date,from_date,to_date,contract_no,property_id,building,items,is_multi=False):
    doc = frappe.get_doc(dict(
		doctype = "Sales Invoice",
		customer = customer,
		posting_date = getdate(from_date),
		period_start_date = getdate(from_date),
		period_end_date = getdate(to_date),
		property = property_id,
		building = building,
		contract_no = contract_no,
		set_posting_time = 1,
		items = items,
		is_property_invoice = 1,
        is_deposite_invoice = 1,
        is_multi_contract_invoice = 0
    )).insert(ignore_permissions = True)
