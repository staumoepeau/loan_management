// Copyright (c) 2017, Sione Taumoepeau and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Product', {

	onload: function(frm) {	
		frm.set_query("interest_account", function() {
			return {
				"filters": {
						"company": frm.doc.company,
						"root_type": "Income",
						"is_group": 0
				}
			};
		});
	},

	refresh: function(frm) {

	}
});
