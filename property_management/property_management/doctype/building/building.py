# -*- coding: utf-8 -*-
# Copyright (c) 2015, shakeel vaim and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Building(Document):
	def validate(self):
		amenities = ""
		for row in self.property_management_amenities:
			amenities += row.amenities + ","
		self.amenities = amenities[:-1] if not amenities == "" else amenities
	def on_submit(self):
		for child in self.get('property_details'):
			for n in range(child.number_of_properties):
				self.create_property(child.property_type,child.area_of_property,child.area_unit)


	def create_property(self,property_type,area=None,area_unit=None):
		property_obj = frappe.get_doc({
						"doctype": "Property",
						"building":self.name,
						"property_type": property_type,
						"block_number":self.block_number,
						"street_name_number":self.street_name_number,
						"area": self.area,
						"total_area_of_property":area,
						"area_unit": area_unit,
						"property_number":self.paci_no
				
		
		})
		property_obj.flags.ignore_mandatory = True
		property_obj.flags.ignore_permissions = True
		property_obj.insert()

	def on_trash(self):
		frappe.db.sql("update tabSeries set current=0 where name='%s-P'" %(self.name))
