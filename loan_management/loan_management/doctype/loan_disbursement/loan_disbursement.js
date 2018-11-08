// Copyright (c) 2018, Sione Taumoepeau and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Disbursement', {
	refresh: function(frm) {
		frm.fields_dict['loan'].get_query = doc => ({
		  filters: { docstatus: 1 },
		});
	},

	loan: async function(frm) {
		const { loan } = frm.doc;
			if (loan) {
				const { message: amount } = await frappe.call({
				method:
					'loan_management.loan_management.api.loan.get_undisbursed_principal',
				args: { loan },
				});
				frm.set_value('disburse_amount', amount);
			}
		},
		disburse_amount: function(frm) {
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
		calculate_totals: function(frm) {
			if (
				frm.fields_dict['total_disbursed'] &&
				frm.fields_dict['total_charges']
			) {
				const { amount = 0, recovered_amount = 0, charges = [] } = frm.doc;
				frm.set_value('total_disbursed', amount);
				frm.set_value(
					'total_charges',
					charges.reduce((a, { charge_amount: x = 0 }) => a + x, 0)
				);
			}
		},
});

