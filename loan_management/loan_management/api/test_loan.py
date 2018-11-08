# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest
import frappe
from frappe.utils import getdate
from gwi_customization.microfinance.api.loan import (
    calculate_principal, update_amounts
)
from gwi_customization.microfinance.doctype.microfinance_loan.\
    test_microfinance_loan import create_test_loan, remove_test_loan
from gwi_customization.microfinance.doctype.microfinance_disbursement.\
    test_microfinance_disbursement import (
        create_test_disbursement, remove_test_disbursement
    )


class TestLoan(unittest.TestCase):
    def tearDown(self):
        remove_test_loan('_Test Loan 1')

    def test_update_amounts(self):
        create_test_loan(
            loan_no='_Test Loan 1',
            loan_principal=50000.0,
            recovery_amount=5000.0,
        )
        update_amounts(
            name='_Test Loan 1',
            principal_amount=60000.0,
            recovery_amount=6000.0
        )
        principal, recovery = frappe.get_value(
            'Microfinance Loan',
            '_Test Loan 1',
            ['loan_principal', 'recovery_amount'],
        )
        self.assertEqual(principal, 60000)
        self.assertEqual(recovery, 6000)

    def test_update_amounts_raises_when_less_than_disbursed(self):
        create_test_loan(
            loan_no='_Test Loan 1',
            loan_principal=50000.0,
            recovery_amount=5000.0,
        )
        create_test_disbursement(
            skip_dependencies=True,
            loan='_Test Loan 1',
            amount=40000.0,
        )
        with self.assertRaises(frappe.exceptions.ValidationError):
            update_amounts(
                name='_Test Loan 1',
                principal_amount=39000.0,
            )
        remove_test_disbursement('_Test Loan 1', keep_dependencies=True)


class TestLoanUtils(unittest.TestCase):
    def test_calculate_principal(self):
        actual = calculate_principal(
            20000.0, '_Test Loan Plan Basic', '2030-08-19', '2017-12-12'
        )
        expected = {
            'principal': 400000.0,
            'expected_eta': getdate('2022-12-31'),
            'duration': 60,
            'recovery_amount': 6666.67,
            'initial_interest': 40000.0,
        }
        self.assertEqual(actual, expected)

    def test_calculate_principal_end_date_before_loan_plan_max_duration(self):
        actual = calculate_principal(
            20000.0, '_Test Loan Plan Basic', '2020-08-19', '2017-12-12',
        )
        expected = {
            'principal': 206666.67,
            'expected_eta': getdate('2020-07-31'),
            'duration': 31,
            'recovery_amount': 6666.67,
            'initial_interest': 21000.0,
        }
        self.assertEqual(actual, expected)

    def test_calculate_principal_force_max_duration(self):
        actual = calculate_principal(
            20000.0, '_Test Loan Plan Eco', '2020-08-19', '2017-12-12'
        )
        expected = {
            'principal': 300000.0,
            'expected_eta': getdate('2022-12-31'),
            'duration': 60,
            'recovery_amount': 5000.0,
            'initial_interest': 15000.0,
        }
        self.assertEqual(actual, expected)
