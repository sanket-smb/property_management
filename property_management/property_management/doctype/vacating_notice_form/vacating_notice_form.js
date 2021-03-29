// Copyright (c) 2020, shakeel vaim and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vacating Notice Form', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__("Make Inspection"), function() {
				frappe.model.open_mapped_doc({
					method: "property_management.property_management.doctype.vacating_notice_form.vacating_notice_form.make_inspection",
					frm: cur_frm
				})
			})
		}
	}
});
