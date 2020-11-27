# -*- coding: utf-8 -*-
# Copyright (c) 2020, shakeel vaim and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PropertyInspection(Document):
	pass

@frappe.whitelist()
def fetch_quality_inspection_readings(name):
	records = frappe.get_doc("Quality Inspection Template", name)
	return records.item_quality_inspection_parameter
