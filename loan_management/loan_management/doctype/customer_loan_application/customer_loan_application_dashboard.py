from frappe import _

def get_data():
    return {
        'chart_data': True, 
        'fieldname': 'loan',
        'transactions': [
            {
                'label': _('Disbursement'),
                'items': ['Loan Disbursement']
            },
            {
                'label': _('Repayment'),
                'items': ['Loan Repayment']
            },
        ]
    }
