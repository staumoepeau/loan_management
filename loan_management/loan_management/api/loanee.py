# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


@frappe.whitelist()
def get_service_details(loanee=None, customer=None):
    if customer:
        results = frappe.db.sql(
            """
                SELECT date_of_retirement, net_salary_amount
                FROM `tabMicrofinance Loanee`
                WHERE customer = '{customer}'
                LIMIT 1
            """.format(customer=customer),
            as_dict=True,
        )
        try:
            return results[0]
        except IndexError:
            return None
    if loanee:
        pass
    return None
