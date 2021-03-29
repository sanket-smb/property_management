// Copyright (c) 2020, shakeel vaim and contributors
// For license information, please see license.txt

frappe.ui.form.on('Multi Property Rent Contract', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1) {
			frm.add_custom_button(__("Make Deposite Invoice"), function() {
				frm.call({
					method:"process_deposite_invoice",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Creating Invoice"),
					callback:function(r){
						frm.reload_doc();
					}
				})
			})
		}
		if(frm.doc.docstatus == 1 && !frm.doc.invoice_created){
			frm.add_custom_button(__("Create Invoice"), function() {
				frm.call({
					method:"process_invoice",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Creating Invoice"),
					callback:function(r){
						frm.reload_doc();
					}
				})
			})
		}
	}
});
