# -*- coding: utf-8 -*-
# Copyright (c) 2018, Sione Taumoepeau and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, get_last_day, add_months, flt, rounded, cint
from functools import partial
from loan_management.loan_management.utils.fp import join, compose, pick

def get_disbursed(loan):
    """Gets disbursed principal"""
    loan_account = frappe.get_value(
        'Customer Loan Application', loan, 'customer_loan_account'
    )
    if not loan_account:
        raise frappe.DoesNotExistError("Loan: {} not found".format(loan))
    conds = [
        "account = '{}'".format(loan_account),
        "voucher_type = 'Loan Disbursement'",
        "against_voucher_type = 'Customer Loan Application'",
         "remarks = 'Loan Disbursement'",
 #       "against_voucher = '{}'".format(loan)
    ]
    return frappe.db.sql(
        """
            SELECT sum(debit) FROM `tabGL Entry` WHERE {}
        """.format(" AND ".join(conds))
    )[0][0] or 0


@frappe.whitelist()
def get_loan_schedule_status(loan, principal_amount, interest_amount, repayment_status):
    """Gets Schesule Status"""

    principal_amount = frappe.db.sql(
        """ Select principal_amount from `tabLoan Repayment Schedule` where parent=%s order by idx""", loan)
    repayment = frappe.get_value(
        'Loan Repayment Schudle', loan, 'loan_amount'
    )
    if not principal_amount:
        raise frappe.DoesNotExistError("Loan: {} not found".format(loan))
    return principal_amount - get_disbursed(loan)

@frappe.whitelist()
def get_payable_interest(loan):
    """Gets Loan Interest Amount"""
    interest_amount = frappe.get_value(
        'Customer Loan Application', loan, 'total_payable_interest'
    )
    if not interest_amount:
        raise frappe.DoesNotExistError("Loan: {} not found".format(loan))
    return interest_amount

@frappe.whitelist()
def get_fees(loan):
    """Gets Loan Fees"""
    fees = frappe.get_value(
        'Customer Loan Application', loan, 'total_fees'
    )
    if not fees:
        raise frappe.DoesNotExistError("Loan: {} not found".format(loan))
    return fees

@frappe.whitelist()
def get_undisbursed_principal(loan):
    """Gets undisbursed principal"""
    principal = frappe.get_value(
        'Customer Loan Application', loan, 'loan_amount'
    )
    if not principal:
        raise frappe.DoesNotExistError("Loan: {} not found".format(loan))
    return principal - get_disbursed(loan)


def get_repayment_principal(loan):
    """Get repayment principal"""
    def get_sum_of(doctype, field):
        def fn(loan):
            return frappe.get_all(
                doctype,
                filters={'docstatus': 1, 'loan': loan},
                fields=field,
            )
        return compose(sum, partial(map, pick(field)), fn)

    return get_sum_of('Loan Repayment', 'total_received')(loan)


@frappe.whitelist()
def get_outstanding_principal(loan, posting_date=None):
    """Get outstanding principal"""
    loan_account = frappe.get_value('Customer Loan Application', loan, 'customer_loan_account')
    cond = [
        "account = '{}'".format(loan_account),
        "voucher_type = 'Loan Disbursement'",
        "against_voucher_type = 'Customer Loan Application'"
    ]
    if posting_date:
        cond.append("posting_date <= '{}'".format(getdate(posting_date)))
    outstanding = frappe.db.sql(
        """
            SELECT sum(debit) - sum(credit)
            FROM `tabGL Entry`
            WHERE {}
        """.format(" AND ".join(cond))
    )[0][0] or 0
    return outstanding - get_repayment_principal(loan)


def get_chart_data(loan_name):
    repayment = get_repayment_principal(loan_name)
    outstanding = get_outstanding_principal(loan_name)
    undisbursed = get_undisbursed_principal(loan_name)

    write_off_account = frappe.get_value(
        'Loan Settings', None, 'write_off_account'
    )
    conds = [
        "account = '{}'".format(write_off_account),
        "against_voucher = '{}'".format(loan_name),
    ]
    wrote_off = frappe.db.sql(
        """
            SELECT SUM(debit - credit) FROM `tabGL Entry` WHERE {conds}
        """.format(
            conds=join(" AND ")(conds)
        )
    )[0][0] or 0

    data = {
        'labels': [
            'RP', 'OS', 'UD', 'Write Off'
        ],
        'datasets': [
            {
                'name': "Total",
                'values': [repayment, outstanding, undisbursed, wrote_off]
            },
        ]
    }
    return data


def update_recovery_status(loan_name, posting_date, status=None):
    """Method update recovery_status of Loan"""
    loan = frappe.get_doc('Customer Loan Application', loan_name)
    outstanding_principal = get_outstanding_principal(
        loan_name, posting_date=posting_date
    )
    current_status = loan.recovery_status
    current_clear = loan.clear_date
    if outstanding_principal == 0 \
            and loan.disbursement_status == 'Fully Disbursed':
        loan.clear_date = posting_date
        loan.recovery_status = 'Repaid'
    else:
        loan.clear_date = None
        if status:
            loan.recovery_status = status
        elif outstanding_principal == loan.loan_principal:
            loan.recovery_status = 'Not Started'
        else:
            loan.recovery_status = 'In Progress'
    if loan.recovery_status != current_status \
            or loan.clear_date != current_clear:
        return loan.save()

@frappe.whitelist()
def get_schedule_info(loan):
    schedule = frappe.db.sql(
        """
            SELECT
                name
            FROM `tabLoan Repayment Schedule`
            WHERE parent='{loan}' AND docstatus = 1 AND (status != "Paid" OR status IS NULL)
            ORDER BY payment_date, idx DESC
            LIMIT 1
        """.format(loan=loan),
        as_dict=True,
    )
    return schedule[0] if schedule else None

@frappe.whitelist()
def update_amounts(name, principal_amount=None, recovery_amount=None):
    loan = frappe.get_doc('Customer Loan Application', name)
    if loan.docstatus != 1:
        frappe.throw('Can only execute on submitted loans')
    if cint(principal_amount) < get_disbursed(name):
        frappe.throw('Cannot set principal less than already disbursed amount')
    if principal_amount:
        loan.update({'total_loan_amount': principal_amount})
    if recovery_amount:
        loan.update({'recovery_amount': recovery_amount})
    loan.save()