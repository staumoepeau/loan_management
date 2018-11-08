# -*- coding: utf-8 -*-
# Copyright (c) 2018, Sione Taumoepeau and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from functools import reduce, partial
import frappe
from frappe import _
from frappe.utils import flt, add_days, getdate
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries
from frappe.model.document import Document
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from loan_management.loan_management.api.loan import update_recovery_status, get_outstanding_principal, get_repayment_principal
from loan_management.loan_management.api.interest import allocate_interests, make_name, update_advance_interests
from loan_management.loan_management.utils.fp import compose, update, join, pick

class LoanRepayment(Document):

	def validate(self):
		if not self.total_fees:
			self.total_fees = self.get_total_fees()
		if not self.total_amount:
			self.total_amount = \
			flt(self.interest_amount) + flt(self.principal_amount)
		if not self.total_received:
			self.total_received = \
			flt(self.total_amount) + flt(self.total_fees)

		account_dict = get_bank_cash_account(
			mode_of_payment=self.mode_of_payment or 'Cash',
			company=self.company,
			)
		self.payment_account = account_dict.get('account')




	def on_submit(self):
		self.create_gl_principal()
		self.update_repayment_schedule()

	def get_total_fees(self):
		loan = frappe.get_doc('Customer Loan Application', self.loan)
		
		if loan.fees_status == "Closed":
			total_fees == 0
		if not loan.fees_status or loan.fees_status == "Open":
			total_fees = loan.total_fees
		
		return total_fees

	def update_repayment_schedule(self):
		loan = frappe.get_doc('Customer Loan Application', self.loan)
		fees_status = loan.fees_status

		if not fees_status or fees_status == "Open":
			frappe.db.sql("""Update `tabCustomer Loan Application` set fees_status="Closed" where name=%s""", (self.loan))
		
		if (loan.total_payable_amount + loan.total_fees) == get_repayment_principal(self.loan):
			frappe.db.sql("""Update `tabCustomer Loan Application` set repayment_status="Repaid" where name=%s""", (self.loan))

		if (loan.total_payable_amount + loan.total_fees) < get_repayment_principal(self.loan):
			frappe.db.sql("""Update `tabCustomer Loan Application` set repayment_status="In Progress" where name=%s""", (self.loan))
		
		if get_repayment_principal(self.loan) == 0:
			frappe.db.sql("""Update `tabCustomer Loan Application` set repayment_status="Not Started" where name=%s""", (self.loan))

		frappe.db.sql(
			"""Update `tabLoan Repayment Schedule` set status = "Paid" where parent=%s AND name=%s""", (self.loan, self.repayment_schedule_id))

	def create_gl_principal(self, cancel=0, adv_adj=0):
		loan = frappe.db.get_value(
			"Customer Loan Application", self.loan, ["interest_income_account", "loan_product","fees_status"], as_dict=True)
		loan_fees = frappe.db.sql(
			"""select loan_fees, description, fee_amount, fees_account from `tabLoan Fees Table` where parent=%s """, 
			(self.loan), as_dict=1)
#		frappe.throw(_("Account - {0}").format(fees))
		cost_center = frappe.db.get_value(
			'Loan Settings', None, 'cost_center'
			)
		fees_entries = sorted(list(loan_fees))
		self.set('loan_fees', [])

		gl_map = []
		if not loan.fees_status or loan.fees_status == "Open":
			for d in fees_entries:
				gl_map.append(
				frappe._dict({
					"posting_date": self.posting_date,
					"account": d.fees_account,
					"debit": d.fee_amount,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
					"against_voucher_type": 'Customer Loan Application',
					"against_voucher": self.loan,
					"remarks" : d.description,
					"cost_center":cost_center
				}))
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": self.payment_account,
				"debit": self.principal_amount,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"remarks" : "Principal Payment",
				"cost_center":cost_center
			}))
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": loan.interest_income_account,
				"debit": self.interest_amount,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"against_voucher_type": 'Customer Loan Application',
				"against_voucher": self.loan,
				"remarks" : "Interest Payment",
				"cost_center":cost_center
			}))
		gl_map.append(
			frappe._dict({
				"posting_date": self.posting_date,
				"account": self.loan_account,
				"credit": self.total_received,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"against": self.customer,
				"party_type": "Customer",
				"party": self.customer,
				"remarks" : "Loan Payment",
				"against_voucher_type": 'Customer Loan Application',
				"against_voucher": self.loan
			}))
		
		if gl_map:
			make_gl_entries(gl_map, cancel=(self.docstatus == 2))
 