# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from datetime import datetime

__version__ = '0.0.1'

def get_month_diff(from_date, to_date):
	end_date = datetime.strptime(str(to_date), '%Y-%m-%d')
	start_date = datetime.strptime(str(from_date), '%Y-%m-%d')
	num_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
	return num_months + 1
