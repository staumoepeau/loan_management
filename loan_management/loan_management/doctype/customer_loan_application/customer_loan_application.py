# -*- coding: utf-8 -*-
# Copyright (c) 2018, Sione Taumoepeau and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, math
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, rounded, add_months, nowdate
from frappe.model.document import Document
from frappe.utils import getdate, get_last_day, cint
from functools import partial
from erpnext.accounts.general_ledger import make_gl_entries
from loan_management.loan_management.api.loan import (
    get_chart_data,
	get_schedule_info,
    get_outstanding_principal,
	get_undisbursed_principal,
)

class CustomerLoanApplication(Document):

	def on_submit(self):
		if self.workflow_state == "Approved":
			self.disbursement_status = "Sanctioned"
		if self.workflow_state == "Rejected":
			self.status = "Rejected"
		if self.workflow_state == "Pending":
			self.status = "Pending"

		self.create_customer_account()
		self.get_loan_accounts()
		self.update_disbursement_status()
		self.update_repayment_status()

	def validate(self):		
		if not self.company:
			self.company = erpnext.get_default_company()
		if not self.posting_date:
			self.posting_date = nowdate()
		self.check_repayment_method()
		self.validate_loan_amount()
		if self.loan_product and not self.rate_of_interest:
			self.rate_of_interest = frappe.db.get_value("Loan Product", self.loan_product, "rate_of_interest")
			self.annual_or_monthly = frappe.db.get_value("Loan Product", self.loan_product, "annual_or_monthly")
		self.get_repayment_details()
		self.calculate_payable_amount()
		self.make_repayment_schedule()
		self.set_repayment_period()
		self.calculate_totals()

	def validate_loan_amount(self):
		maximum_loan_limit = frappe.db.get_value('Loan Product', self.loan_product, 'maximum_loan_amount')
		if maximum_loan_limit and self.loan_amount > maximum_loan_limit:
			frappe.throw(_("Loan Amount cannot exceed Maximum Loan Amount of {0}").format(maximum_loan_limit))

	def get_repayment_details(self):
		if self.repayment_method == "Repay Over Number of Periods":
			self.monthly_repayment_amount = self.get_monthly_repayment_amount()
	
	def calculate_payable_amount(self):
		balance_amount = self.loan_amount
		self.total_payable_amount = 0
		self.total_payable_interest = 0
		if self.annual_or_monthly == "Monthly":
			interest_amount = rounded(balance_amount * flt(self.rate_of_interest) / (12*100))			
		if self.annual_or_monthly == "Yearly":
			interest_amount = rounded(balance_amount * flt(self.rate_of_interest) / (100))
			
		self.total_payable_interest += interest_amount	
		self.total_payable_amount = self.loan_amount + self.total_payable_interest

	def make_repayment_schedule(self):
		self.repayment_schedule = []
		payment_date = self.repayment_start_date
		balance_amount = self.loan_amount

		while(balance_amount > 0):
			if self.annual_or_monthly == "Monthly":
				interest_amount = rounded(balance_amount * flt(self.rate_of_interest) / (12*100))			
			if self.annual_or_monthly == "Yearly":
				interest_amount = rounded(balance_amount * flt(self.rate_of_interest) / (100))

			principal_amount = self.total_payable_amount - interest_amount
			balance_amount = rounded(balance_amount + interest_amount - self.total_payable_amount)
			fee_amount = (self.total_fees / self.repayment_periods)

#			principal_amount = self.loan_amount
#			balance_amount = rounded(balance_amount + interest_amount)

			if balance_amount < 0:
				principal_amount += balance_amount
				balance_amount = 0.0

			total_payment = principal_amount + interest_amount


			self.append("repayment_schedule", {
				"payment_date": payment_date,
				"principal_amount": principal_amount,
				"interest_amount": interest_amount,
				"total_payment": total_payment,
				"total_fee_amount" : fee_amount,
				"balance_loan_amount": balance_amount,
				"status" : "Unpaid"
			})

			next_payment_date = add_months(payment_date, 1)
			payment_date = next_payment_date

	def set_repayment_period(self):
		if self.repayment_method == "Repay Fixed Amount per Period":
			repayment_periods = len(self.repayment_schedule)

			self.repayment_periods = repayment_periods

	def calculate_totals(self):
		if not self.total_loan:
			self.total_loan = self.total_fees + self.total_payable_amount
#		self.total_payment = 0
#		self.total_interest_payable = 0
#		for data in self.repayment_schedule:
#			self.total_payment += data.total_payment
#			self.total_interest_payable +=data.interest_amount
	
	def update_disbursement_status(self):
		disbursement = frappe.db.sql("""select posting_date, ifnull(sum(debit_in_account_currency), 0) as disbursed_amount 
			from `tabGL Entry` where against_voucher_type="Customer Loan Appliaction" and against_voucher = %s""", 
			(self.name), as_dict=1)[0]
		if disbursement.disbursed_amount == self.loan_amount:
			frappe.db.set_value("Customer Loan Application", self.name , "disbursement_status", "Fully Disbursed")
			frappe.db.sql("""Update `tabCustomer Loan Application` set status="Fully Disbursed" where name = %s """, (self.name))
			frappe.throw(_("Fully Disbursed - {0}").format(self.name))
		if disbursement.disbursed_amount < self.loan_amount and disbursement.disbursed_amount != 0:
			frappe.db.set_value("Customer Loan Application", self.name , "disbursement_status", "Partially Disbursed")
			frappe.throw(_("Partially Disbursed"))
		if disbursement.disbursed_amount == 0:
#			frappe.throw(_("Sanctioned"))
			frappe.db.set_value("Customer Loan Application", self.name , "disbursement_status", "Sanctioned")
		if disbursement.disbursed_amount > self.loan_amount:
			frappe.throw(_("Disbursed Amount cannot be greater than Loan Amount {0}").format(self.loan_amount))
		if disbursement.disbursed_amount > 0:
			frappe.db.sql("""Update `tabCustomer Loan Application` set disbursement_date="Partially Disbursed" where name=%s """, self.name)
			frappe.db.set_value("Customer Loan Application", self.name , "disbursement_date", disbursement.posting_date)

	def update_repayment_status(self):
		if self.repayment_amount == 0:
			frappe.db.set_value("Customer Loan Application", self.name , "repayment_status", "Not Started")
		if self.repayment_amount < self.total_payable_amount and self.repayment_amount != 0:
			frappe.db.set_value("Customer Loan Application", self.name , "repayment_status", "In Progress")
		if self.repayment_amount == self.total_payable_amount:
			frappe.db.set_value("Customer Loan Application", self.name , "repayment_status", "Repaid")

	def check_repayment_method(self):
		if self.repayment_method == "Repay Over Number of Periods" and not self.repayment_periods:
			frappe.throw(_("Please enter Repayment Periods"))
			
#		if self.repayment_method == "Repay Fixed Amount per Period":
#			if not self.monthly_repayment_amount:
#				frappe.throw(_("Please enter repayment Amount"))
#			if self.monthly_repayment_amount > self.loan_amount:
#				frappe.throw(_("Monthly Repayment Amount cannot be greater than Loan Amount"))

	def get_monthly_repayment_amount(self):
		if self.rate_of_interest:
			if self.annual_or_monthly == "Monthly":
				monthly_interest_rate = flt(self.rate_of_interest) / (12 *100)			
			if self.annual_or_monthly == "Yearly":
				monthly_interest_rate = flt(self.rate_of_interest) / (100)

			monthly_repayment_amount = math.ceil(flt(self.total_payable_amount) / self.repayment_periods)
#			monthly_interest_rate = flt(self.rate_of_interest) / (12 *100)			
#			monthly_repayment_amount = math.ceil((self.loan_amount * monthly_interest_rate * 
#				(1 + monthly_interest_rate)**self.repayment_periods) \
#				/ ((1 + monthly_interest_rate)**self.repayment_periods - 1))
		else:
			monthly_repayment_amount = math.ceil(flt(self.loan_amount) / self.repayment_periods)
		return monthly_repayment_amount

	def create_customer_account(self):
		#Take the ' off the Customer Name
		self.customer = self.customer.replace("'","")
		company = frappe.db.get_value("Company", self.company, ["abbr", "name"], as_dict=True)
		doc = frappe.new_doc('Account')
		doc.company = self.company
		doc.root_type = "Asset"
		doc.report_type = "Balance Sheet"
		doc.account_currency = "TOP"
		doc.parent_account = "Customer Loan - " + company.abbr
		doc.account_name = self.customer + " - " + self.name
		doc.save(ignore_permissions=True)
		doc.submit()

	def get_loan_accounts(self):
		company = frappe.db.get_value("Company", self.company, ["abbr", "name"], as_dict=True)
		account_interest = frappe.db.get_value("Loan Product", self.loan_product, "interest_account")
		customer_account = self.customer.replace("'","") + " - " + self.name + " - " + company.abbr
		if not self.customer_loan_account:
			frappe.db.set_value("Customer Loan Application", self.name , "customer_loan_account", customer_account)
		if not self.interest_income_account:
			frappe.db.set_value("Customer Loan Application", self.name , "interest_income_account", account_interest)
	
	def get_interest_amount(self):
		balance_amount = self.loan_amount
		if self.annual_or_monthly == "Yearly":
			interest_amount = flt(self.rate_of_interest) / (100)
		if self.annual_or_monthly == "Monthly":
			interest_amount = flt(self.rate_of_interest) / (12 * 100)

		return interest_amount

	def onload(self):
         if self.docstatus == 1:
            self.set_onload(
                'chart_data', get_chart_data(self.name)
            )
            self.set_onload(
                'outstanding_principal', get_outstanding_principal(self.name)
            )

@frappe.whitelist()
def create_disbursement(customer_loan, company, loan_account, customer, loan_amount, payment_account):
	undisburse_balance = get_undisbursed_principal(customer_loan)
	disbursement = frappe.new_doc('Loan Disbursement')
	disbursement.loan = customer_loan
	disbursement.customer = customer
	disbursement.loan_account = loan_account
	disbursement.company = company
	disbursement.posting_date = nowdate()
	disbursement.disburse_amount = undisburse_balance
#	frappe.throw(_("Un Disbursed Amount {0}").format(get_undisbursed_principal(customer_loan)))
	return disbursement

@frappe.whitelist()
def create_repayment(customer_loan, company, loan_account, customer, loan_amount):
	schedule = get_schedule_info(customer_loan)
#	frappe.throw(_("Loan Schedule {0}").format(get_schedule_info(customer_loan)))
	loan = frappe.db.get_value("Loan Repayment Schedule",schedule,["name", "principal_amount", "interest_amount"], as_dict=True)
	
	repayment = frappe.new_doc('Loan Repayment')
	repayment.loan = customer_loan
	repayment.customer = customer
	repayment.loan_account = loan_account
	repayment.company = company
	repayment.posting_date = nowdate()
	repayment.principal_amount = loan.principal_amount
	repayment.interest_amount = loan.interest_amount
	repayment.repayment_schedule_id = loan.name

	return repayment


@frappe.whitelist()
def update_amounts(name, loan_amount=None):
	loan = frappe.get_doc('Customer Loan Application', name)
	if loan.docstatus != 1:
		frappe.throw('Can only execute on submitted loans')
	if cint(loan_amount) < get_disbursed(name):
		frappe.throw('Cannot set principal less than already disbursed amount')
	if principal_amount:
		loan.update({'loan_amount': loan_amount})
#    if recovery_amount:
#        loan.update({'recovery_amount': recovery_amount})
	loan.save()

@frappe.whitelist()
def get_disbursed(loan):
	"""Gets disbursed principal"""
	customer_loan_account = frappe.get_value(
		'Customer Loan Appliaction', loan, 'customer_loan_account'
	)
	if not customer_loan_account:
		raise frappe.DoesNotExistError("Loan: {} not found".format(loan))
	conds = [
		"account = '{}'".format(customer_loan_account),
		"against_voucher_type = 'Customer Loan Application'",
		"against_voucher = '{}'".format(loan)
	]
	return frappe.db.sql(
		"""
			SELECT sum(debit) FROM `tabGL Entry` WHERE {}
		""".format(" AND ".join(conds))
	)[0][0] or 0