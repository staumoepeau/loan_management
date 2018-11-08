# -*- coding: utf-8 -*-
# Copyright (c) 2018, Sione Taumoepeau and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from functools import reduce
import frappe
from frappe import _
from frappe.utils import flt, getdate, fmt_money
from erpnext.controllers.accounts_controller import AccountsController
from frappe.model.document import Document
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from loan_management.loan_management.api.loan import get_undisbursed_principal


class LoanDisbursement(Document):

	def on_submit(self):
		self.make_entries()
		self.update_loan_status()
		
	def validate(self):
		to_disburse = flt(self.disburse_amount)
		if to_disburse > get_undisbursed_principal(self.loan):
			frappe.throw(
				"Disbursed amount cannot exceed the sanctioned amount"
				)
		loan_start_date = frappe.get_value(
			'Customer Loan Appliaction', self.loan, 'repayment_start_date'
			)
 #       if getdate(self.posting_date) < loan_start_date:
 #           frappe.throw("Cannot disburse before loan start date")

	def before_save(self):
		self.total_disbursed = flt(self.disburse_amount)

		account_dict = get_bank_cash_account(
			mode_of_payment=self.mode_of_payment or 'Cash',
			company=self.company,
			)
		self.payment_account = account_dict.get('account')


	def on_cancel(self):
		self.make_entries(cancel=1)
		self.update_loan_status()


	def make_entries(self, cancel=0, adv_adj=0):
		gl_map = []
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": self.loan_account,
				"debit": self.disburse_amount,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"remarks" : "Loan Disbursement",
				"against_voucher_type": 'Customer Loan Application',
				"against_voucher": self.loan
			}))
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": self.payment_account,
				"credit": self.disburse_amount,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"against": self.customer,
				"party_type": "Customer",
				"party": self.customer,
				"against_voucher_type": 'Customer Loan Application',
				"against_voucher": self.loan
			}))
		
		if gl_map:
			make_gl_entries(gl_map, cancel=(self.docstatus == 2))
		
	
	

	def update_loan_status(self):
		"""Method to update disbursement_status of Loan"""
		loan = frappe.get_doc('Customer Loan Application', self.loan)
		undisbursed_principal = get_undisbursed_principal(self.loan)
		current_status = loan.disbursement_status
		fees_status = loan.fees_interest_rate_status
		
		if not fees_status or fees_status == "Open":
			self.make_fees()
			self.interest_entries()
			frappe.db.sql("""Update `tabCustomer Loan Application` set fees_interest_rate_status="Closed" where name=%s""", (self.loan))
		if loan.loan_amount > undisbursed_principal > 0:
			frappe.db.sql("""Update `tabCustomer Loan Application` set disbursement_status="Partially Disbursed" where name=%s""", (self.loan))
		elif loan.loan_amount == undisbursed_principal:
			frappe.db.sql("""Update `tabCustomer Loan Application` set disbursement_status="Sanctioned" where name=%s""", (self.loan))
		elif undisbursed_principal == 0:
			frappe.db.sql("""Update `tabCustomer Loan Application` set disbursement_status="Fully Disbursed" where name=%s""", (self.loan))
		if loan.disbursement_status != current_status:
			loan.save()
	
	def make_fees(self):
		loan_fees = frappe.db.sql(
			"""select loan_fees, description, fee_amount, fees_account from `tabLoan Fees Table` where parent=%s """, 
			(self.loan), as_dict=1)
		loan = frappe.get_doc(
			'Customer Loan Application', self.loan
			)
		cost_center = frappe.db.get_value(
			'Loan Settings', None, 'cost_center'
			)
		fees_entries = sorted(list(loan_fees))
		self.set('loan_fees', [])

		gl_map = []
		for d in fees_entries:
			gl_map.append(
				frappe._dict({
					"posting_date": self.posting_date,
					"account": d.fees_account,
					"credit": d.fee_amount,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
					"remarks" : d.description,
					"cost_center":cost_center
				}))
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": self.loan_account,
				"debit": loan.total_fees,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"against": self.customer,
				"against_voucher_type": 'Customer Loan Application',
				"against_voucher": self.loan,
				"remarks" : "Loan Fees"
			}))
		if gl_map:
			make_gl_entries(gl_map, cancel=(self.docstatus == 2))
	
	def interest_entries(self):
		loan = frappe.get_doc('Customer Loan Application', self.loan)
		cost_center = frappe.db.get_value(
			'Loan Settings', None, 'cost_center'
			)
		
		gl_map = []
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": loan.interest_income_account,
				"credit": loan.total_payable_interest,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"remarks" : "Loan Interest",
				"cost_center":cost_center
			}))
		
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": self.loan_account,
				"debit": loan.total_payable_interest,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"against": self.customer,
				"against_voucher_type": 'Customer Loan Application',
				"against_voucher": self.loan,
				"remarks" : "Loan Interest"

			}))

		if gl_map:
			make_gl_entries(gl_map, cancel=(self.docstatus == 2))