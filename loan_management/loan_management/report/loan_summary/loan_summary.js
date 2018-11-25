// Copyright (c) 2016, Sione Taumoepeau and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Loan Summary"] = {
	filters: [
	  {
		fieldname: 'display',
		label: __('Display'),
		fieldtype: 'Select',
		options: 'Existing Loans\nAll Loans',
		default: 'Existing Loans',
	  },
	  {
		fieldname: 'loan_product',
		label: __('Loan Product'),
		fieldtype: 'Link',
		options: 'Loan Product',
	  },
	],
  };
  