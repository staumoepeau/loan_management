# Copyright (c) 2013, Sione Taumoepeau and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

from loan_management.loan_management.api.loan import (
    get_undisbursed_principal,
    get_outstanding_principal,
    get_repayment_principal,
	get_fees, get_payable_interest,
)


def _make_row(row):
	loan, sanctioned = row[1], row[3]
	undisbursed = get_undisbursed_principal(loan)
	outstanding = get_outstanding_principal(loan)
	repayment = get_repayment_principal(loan)
	fee = get_fees(loan)
	interest = get_payable_interest(loan)
	return row + (
		sanctioned - undisbursed,
		fee,
		interest,
		repayment,
		outstanding,
	)


def execute(filters={}):
    columns = [
            _("Posting Date") + ":Date:90",
            _("Loan ID") + ":Link/Customer Loan Application:90",
            _("Customer") + ":Link/Customer:120",
            _("Loan Amount") + ":Currency/currency:90",
            _("Disbursed Amount") + ":Currency/currency:90",
			_("Fees Amount") + ":Currency/currency:90",
			_("Interest Amount") + ":Currency/currency:90",
            _("Repayment Amount") + ":Currency/currency:90",
            _("Outstanding Amount") + ":Currency/currency:90",
        ]

    conds = [
        "docstatus = 1",
    ]
    if filters.get('display') == 'Existing Loans':
        conds.append(
            "repayment_status in ('Not Started', 'In Progress')"
        )
    if filters.get('loan_product'):
        conds.append(
            "loan_product = '{}'".format(filters.get('loan_product'))
        )
    result = frappe.db.sql(
        """
            SELECT posting_date, name, customer, loan_amount
            FROM `tabCustomer Loan Application`
            WHERE {}
        """.format(" AND ".join(conds))
    )
    data = map(_make_row, result)

    return columns, data

