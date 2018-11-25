// Copyright (c) 2017, Sione Taumoepeau and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Loan Application', {

	on_submit: function(frm){
 
            frappe.set_route("List", "Customer Loan Application")
            location.reload(true);

    },
	onload: function(frm) {	

	},

	refresh: async function(frm) {
    frm.trigger('clear_chart');
		if (frm.doc.docstatus === 1 && frm.doc.__onload['chart_data']) {
			frm.trigger('render_chart');
		  }

		if (frm.doc.docstatus > 0) {
			frm.set_df_property('loan_amount', 'read_only', 1);
			frm.page.add_menu_item(__('Account Statement'), function() {
			  frappe.set_route('query-report', 'Loan Account Statement', {
				loan : frm.doc['name'],
			  });
			});
		}
		
		if (frm.doc.docstatus == 1 && (frm.doc.disbursement_status == "Sanctioned" || frm.doc.disbursement_status == "Partially Disbursed")) {	
			frm.page.add_menu_item(__('Loan Disbursement'), function() {
				frm.trigger("make_disbursement");
			});
		}
		if (frm.doc.docstatus == 1 && frm.doc.repayment_start_date && frm.doc.repayment_status != "Repaid") {	
			frm.page.add_menu_item(__('Make Repayment'), function() {
				frm.trigger("make_repayment");
			});
		}

		frm.trigger("toggle_fields")
		frm.trigger("add_toolbar_buttons")
	},

	make_disbursement: function(frm) {
		frappe.call({
			args: {
				"customer_loan": frm.doc.name,
				"company": frm.doc.company,
				"loan_account": frm.doc.customer_loan_account,
				"customer": frm.doc.customer,
				"loan_amount": frm.doc.loan_amount,
				"payment_account": frm.doc.payment_account
			},
			method: "loan_management.loan_management.doctype.customer_loan_application.customer_loan_application.create_disbursement",
			callback: function(r) {
				if (r.message)
					var doc = frappe.model.sync(r.message)[0];
					frappe.set_route("Form", doc.doctype, doc.name);
			}
		})
	},
	make_repayment: function(frm) {
		frappe.call({
			args: {
				"customer_loan": frm.doc.name,
				"company": frm.doc.company,
				"loan_account": frm.doc.customer_loan_account,
				"customer": frm.doc.customer,
				"loan_amount": frm.doc.loan_amount
			},
			method: "loan_management.loan_management.doctype.customer_loan_application.customer_loan_application.create_repayment",
			callback: function(r) {
				if (r.message)
					var doc = frappe.model.sync(r.message)[0];
					frappe.set_route("Form", doc.doctype, doc.name);
			}
		})
	},

	repayment_method: function(frm) {
		frm.doc.repayment_amount = frm.doc.repayment_periods = ""
		frm.trigger("toggle_fields")
	},
	toggle_fields: function(frm) {
		frm.toggle_enable("repayment_amount", frm.doc.repayment_method=="Repay Fixed Amount per Period")
		frm.toggle_enable("repayment_periods", frm.doc.repayment_method=="Repay Over Number of Periods")
	},
	disbursement_date: function(frm) {
		frm.trigger('set_disbursement_date');
		
		

	},
	render_chart: function(frm) {
		const chart_area = frm.$wrapper.find('.form-graph').removeClass('hidden');
		const chart = new frappeChart.Chart(chart_area[0], {
		  type: 'percentage',
		  data: frm.doc.__onload['chart_data'],
		  colors: ['green', 'orange', 'blue', 'grey'],
		});
		},
	  clear_chart: function(frm) {
			frm.$wrapper
				.find('.form-graph')
				.empty()
				.addClass('hidden');
		},
	
	set_disbursement_date: function(frm){	
		frm.set_value("repayment_start_date", frappe.datetime.add_days(frm.doc.disbursement_date, frm.doc.loan_period));
		refresh_field("repayment_start_date");
	//	frappe.msgprint(__("Test."));
	},
});

frappe.ui.form.on("Loan Fees Table", "loan_fees", function(frm, cdt, cdn){
	var d = locals[cdt][cdn];

	frappe.call({
		"method": "frappe.client.get",
		args: {
			doctype: "Loan Fees",
			filters: {
				'name': d.loan_fees
			},
		},
		callback: function(data) {
			frappe.model.set_value(d.doctype, d.name, "description", data.message["fee_name"]);
			frappe.model.set_value(d.doctype, d.name, "fee_amount", data.message["fee_amount"]);
			frappe.model.set_value(d.doctype, d.name, "fees_account", data.message["fee_account"]);
		}
	})
});

frappe.ui.form.on("Loan Fees Table", "fee_amount", function(frm, cdt, cdn){
	var d = locals[cdt][cdn];
	var total_fees_amount = 0;

	frm.doc.loan_fees_table.forEach(function(d) { 

		total_fees_amount += d.fee_amount;

		});

	frm.set_value("total_fees", total_fees_amount);

	refresh_field("total_fees");
	refresh_field("loan_amount");
});

frappe.ui.form.on("Customer Income", "income_amount", function(frm, cdt, cdn){
	var t = locals[cdt][cdn];
	var total_income_amount = 0;

	frm.doc.customer_income.forEach(function(t) { 

		total_income_amount += t.income_amount;

		});
	frm.set_value("total_income", total_income_amount);
	refresh_field("total_income");

});

frappe.ui.form.on("Customer Expenses", "income_amount", function(frm, cdt, cdn){
	var e = locals[cdt][cdn];
	var total_expenses_amount = 0;

	frm.doc.customer_expenses.forEach(function(e) { 

		total_expenses_amount += t.expenses_amount;

		});
	frm.set_value("total_expenses", total_expenses_amount);
	refresh_field("total_expenses");

});