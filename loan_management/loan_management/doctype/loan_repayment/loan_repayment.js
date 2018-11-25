// Copyright (c) 2018, Sione Taumoepeau and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Repayment', {
	refresh: function(frm) {
			frm.fields_dict['loan'].get_query = doc => ({
				filters: { docstatus: 1 },
			});
		},
	  loan: function(frm) {
		frm.trigger('set_init_amounts');
	  },
	  posting_date: function(frm) {
		frm.trigger('set_init_amounts');
	  },
	  principal_amount: function(frm) {
		frm.trigger('calculate_totals');
	  },
	  total_interests: function(frm) {
		frm.trigger('calculate_totals');
	  },
	  mode_of_payment: async function(frm) {
		const { mode_of_payment, company } = frm.doc;
		frm.toggle_reqd(['cheque_no', 'cheque_date'], mode_of_payment == 'Cheque');
		const { message } = await frappe.call({
		  method:
			'erpnext.accounts.doctype.sales_invoice.sales_invoice.get_bank_cash_account',
		  args: { mode_of_payment, company },
		});
		if (message) {
		  frm.set_value('payment_account', message.account);
		}
	  },
//	  set_init_amounts: async function(frm) {
//		const { loan, posting_date } = frm.doc;
//		if (loan && posting_date) {
//		  const [
//			{ message: interest_amount = 0 },
//			{ message: { monthly_repayment_amount = 0 } = {} },
//		  ] = await Promise.all([
//			frappe.call({
//			  method:
//				'loan_management.loan_management.api.interest.get_current_interest',
//			  args: { loan, posting_date },
//			}),
//			frappe.db.get_value('Customer Loan Application', loan, ['monthly_repayment_amount'],['total_fees']),
//		  ]);
//		  frm.set_value('total_interests', interest_amount);
//			frm.set_value('principal_amount', monthly_repayment_amount);
//			frm.set_value('total_fees', total_fees);
//		}
//	  },
		
		calculate_totals: function(frm) {
		if (
		  frm.fields_dict['interest_amount'] &&
		  frm.fields_dict['total_fees']
		) {
		  const {
				interest_amount = 0,
			principal_amount = 0,
			charges = [],
		  } = frm.doc;
		  const total_amount = interest_amount + principal_amount;
		  const total_fees = charges.reduce(
			(a, { charge_amount: x = 0 }) => a + x,
			0
		  );
		  frm.set_value('total_amount', interest_amount + principal_amount);
		  frm.set_value('total_fees', total_fees);
		  frm.set_value('total_received', total_amount + total_fees);
		}
	  },
	});
	