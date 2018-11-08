# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest
from frappe.utils import getdate
from gwi_customization.microfinance.api.interest import (
    _interest_to_period, _allocate, _generate_periods
)


class TestInterest(unittest.TestCase):
    def test_interest_to_period(self):
        actual = _interest_to_period({
            'period': 'Aug, 2017',
            'start_date': '2017-08-19',
            'end_date': '2017-08-31',
            'billed_amount': 2000.0,
            'paid_amount': 500.0,
        })
        expected = {
            'period_label': 'Aug, 2017',
            'start_date': '2017-08-19',
            'end_date': '2017-08-31',
            'billed_amount': 2000.0,
            'outstanding_amount': 1500.0,
            'ref_interest': None,
        }
        self.assertEqual(expected, actual)

    def test_allocate(self):
        period = _allocate({
            'billed_amount': 2000.0,
            'outstanding_amount': 1500.0,
        }, 2000.0)
        self.assertEqual(period.get('allocated_amount'), 1500.0)

    def test_allocate_lesser_amount(self):
        period = _allocate({
            'billed_amount': 2000.0,
            'outstanding_amount': 1500.0,
        }, 1000.0)
        self.assertEqual(period.get('allocated_amount'), 1000.0)

    def test_generate_periods(self):
        periods = _generate_periods('2017-08-19')
        period = {}
        for _ in range(0, 4):
            period = periods.next()
        self.assertEqual(period.get('period_label'), 'Nov 2017')
        self.assertEqual(period.get('start_date'), getdate('2017-11-01'))
        self.assertEqual(period.get('end_date'), getdate('2017-11-30'))
