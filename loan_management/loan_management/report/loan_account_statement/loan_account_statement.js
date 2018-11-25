// Copyright (c) 2018, Sione Taumoepeau and contributors
// For license information, please see license.txt


frappe.query_reports['Loan Account Statement'] = {
	filters: [
	  {
		fieldname: 'from_date',
		label: __('From Date'),
		fieldtype: 'Date',
		default: frappe.datetime.month_start(),
		reqd: 1,
	  },
	  {
		fieldname: 'to_date',
		label: __('To Date'),
		fieldtype: 'Date',
		default: frappe.datetime.month_end(),
		reqd: 1,
	  },
	  {
		fieldname: 'loan',
		label: __('Loan'),
		fieldtype: 'Link',
		options: 'Customer Loan Application',
		get_query: function() {
		  return { doctype: 'Customer Loan Application', filters: { docstatus: 1 } };
		},
		on_change: async function() {
		  const loan = frappe.query_report_filters_by_name['loan'].get_value();
		  const { message = {} } = await frappe.db.get_value(
			'Customer Loan Application',
			loan,
			['customer_name', 'posting_date']
		  );
		  frappe.query_report_filters_by_name['customer_name'].set_value(
			message['customer_name']
		  );
		  frappe.query_report_filters_by_name['loan_start_date'].set_value(
			message['posting_date']
		  );
		},
		reqd: 1,
	  },
	  {
		fieldname: 'customer_name',
		label: __('Customer Name'),
		fieldtype: 'Data',
		hidden: 1,
	  },
	  {
		fieldname: 'loan_start_date',
		label: __('Loan Start Date'),
		fieldtype: 'Date',
		hidden: 1,
	  },
	],
  };
  