# -*- coding: utf-8 -*-
# Copyright (c) 2017, Sione Taumoepeau and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.controllers.accounts_controller import AccountsController

class LoanProduct(AccountsController):
	
	def validate(self):
		if not self.product_code:
			self.product_code = self.name
		if not self.product_name:
			self.product_name = self.product_type + " Loan - " + self.name

	