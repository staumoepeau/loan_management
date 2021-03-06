from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Loan"),
			"icon": "fa fa-table",
			"items": [
				{
					"type": "doctype",
					"name": "Customer Loan Application",
					"label": _("Loan Application")
				},
				{
					"type": "doctype",
					"name": "Customer",
					"label": _("Customer")
				}
			]

		},
		{
			"label": _("Transactions"),
			"icon": "fa fa-table",
			"items": [
				{
					"type": "doctype",
					"name": "Loan Disbursement",
					"label": _("Loan Disbursement")
				},
				{
					"type": "doctype",
					"name": "Loan Repayment",
					"label": _("Loan Repayment")
				},
			]

		},
		{
			"label": _("Setting"),
			"icon": "fa fa-table",
			"items": [
				{
					"type": "doctype",
					"name": "Loan Settings",
					"label": _("Loan Settings")
				},
				{
					"type": "doctype",
					"name": "Loan Product",
					"label": _("Loan Product")
				},
				{
					"type": "doctype",
					"name": "Loan Fees",
					"label": _("Loan Fees")
				},
			]

		},
		{
			"label": _("Loan Assets"),
			"icon": "fa fa-table",
			"items": [
				{
					"type": "doctype",
					"name": "Loan Assets",
					"label": _("Loan Assets")
				},
			]

		},
		{
			"label": _("Reports"),
			"items": [
				{
                    "type": "report",
                    "is_query_report": True,
                    "name": "Loan Account Statement",
                    "label": "Loan Statement",
                },
				                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Loan Summary",
                    "label": "Loan Summary",
                },
			]

		}
    ]        