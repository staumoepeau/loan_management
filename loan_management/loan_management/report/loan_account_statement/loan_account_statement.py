# Copyright (c) 2013, Sione Taumoepeau and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from functools import reduce, partial
from loan_management.loan_management.utils.fp import compose, join
from loan_management.loan_management.api.loan import get_outstanding_principal


def _accum_reducer(acc, row):
    return acc + [
        row[:-1] + (acc[-1][5] + row[4],) + row[-1:]
    ]


def _col_sum(idx):
    def fn(rows):
        return reduce(lambda a, x: a + x[idx], rows, 0)
    return fn


_stringify_accounts = compose(
    join(', '), partial(map, lambda x: "'{}'".format(x))
)


def execute(filters={}):
    columns = [
        _("Posting Date") + ":Date:90",
        _("Account") + ":Link/Account:240",
        _("Credit") + ":Currency/currency:90",
        _("Debit") + ":Currency/currency:90",
        _("Amount") + ":Currency/currency:90",
        _("Cummulative") + ":Currency/currency:90",
        _("Remarks") + "::240",
    ]

    loan_account = frappe.get_value(
        'Customer Loan Application', filters.get('loan'), ['customer_loan_account']
    )
#    accounts_to_exclude = [
#        'Personal Loan Interest - {}'.format(
#            frappe.db.get_value('Company', company, 'abbr')
#        ),
#        'Cash - {}'.format(
 #           frappe.db.get_value('Company', company, 'abbr')
#        ),
#        'Temporary Opening - {}'.format(
#            frappe.db.get_value('Company', company, 'abbr')
#        )
#    ]
    conds = [
        "against_voucher_type = 'Customer Loan Application'",
        "against_voucher = '{}'".format(filters.get('loan')),
        "account = '{}'".format(loan_account),
#        "account NOT IN ({})".format(
#            _stringify_accounts(accounts_to_exclude)
#        ),
    ]
    opening_entries = frappe.db.sql(
        """
            SELECT
                sum(credit) AS credit,
                sum(debit) AS debit,
                sum(credit - debit) as amount
            FROM `tabGL Entry`
            WHERE {conds} AND posting_date <'{from_date}'
        """.format(
            conds=join(" AND ")(conds),
            from_date=filters.get('from_date'),
        ),
        as_dict=True,
    )[0]
    results = frappe.db.sql(
        """
            SELECT
                posting_date,
                account,
                sum(credit) as credit,
                sum(debit) as debit,
                sum(credit - debit) as amount,
                remarks
            FROM `tabGL Entry`
            WHERE {conds}
            AND posting_date BETWEEN '{from_date}' AND '{to_date}'
            GROUP BY posting_date, account, voucher_no, remarks
            ORDER BY posting_date ASC, name ASC
        """.format(
            conds=join(" AND ")(conds),
            from_date=filters.get('from_date'),
            to_date=filters.get('to_date'),
        )
    )

    opening_credit = opening_entries.get('credit') or 0
    opening_debit = opening_entries.get('debit') or 0
    opening_amount = opening_entries.get('amount') or 0
    total_credit = _col_sum(2)(results)
    total_debit = _col_sum(3)(results)
    total_amount = _col_sum(4)(results)
    opening = (
        None,
        _("Opening"),
        opening_credit,
        opening_debit,
        opening_amount,
        opening_amount,
        None,
    )
    total = (
        None,
        _("Total"),
        total_credit,
        total_debit,
        total_amount,
        None,
        None
    )
    closing = (
        None,
        _("Closing"),
        opening_credit + total_credit,
        opening_debit + total_debit,
        opening_amount + total_amount,
        get_outstanding_principal(filters.get('loan'), filters.get('to_date')),
        None
    )
    data = reduce(_accum_reducer, results, [opening]) + [total, closing]

    return columns, data
