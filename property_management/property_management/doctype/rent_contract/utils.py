
import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import (getdate, cint, date_diff, cstr)
import math
import frappe

def get_number_months_days(end_date=None, start_date=None):
	date = getdate(end_date)+relativedelta(months=0, days =+ 1)
	diff = relativedelta(getdate(date), getdate(start_date))
	if diff.years >= 1:
		return 12 * diff.years + diff.months, diff.days
	else:
		return diff.months, diff.days

@frappe.whitelist()
def number_of_months(end_date=None, start_date=None):
	return get_number_months_days(end_date, start_date)
