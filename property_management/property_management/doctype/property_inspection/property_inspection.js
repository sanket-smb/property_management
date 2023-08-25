
// Copyright (c) 2020, shakeel vaim and contributors
// For license information, please see license.txt

frappe.ui.form.on('Property Inspection', {
	// refresh: function(frm) {

	// }
});


frappe.ui.form.on("Property Inspection", "quality_inspection_template", function(frm, cdt, cdn) {
    var cocpf_id = cur_frm.doc.quality_inspection_template;
    //var readings = fetch_cocpf_readings(cocpf_id);
    frappe.call({
        method: "property_management.property_management.doctype.property_inspection.property_inspection.fetch_quality_inspection_readings",
        args: {
            "name": cocpf_id
        },
        async: false,
        callback: function(r) {
            if (r.message) {
                console.log("readings------------::" + JSON.stringify(r.message));
		cur_frm.clear_table("readings");
		var readings = r.message;
		for (var i=0;i<readings.length;i++){
			console.log("specification------------::" + readings[i]['specification']);
			var child = cur_frm.add_child("readings");
			frappe.model.set_value(child.doctype, child.name, "specification", readings[i]['specification']);
			frappe.model.set_value(child.doctype, child.name, "value", readings[i]['value']);
		}//end of for loop...
		 refresh_field("readings");
            }
        } //end of callback fun..
    }) //end of frappe call..
});
