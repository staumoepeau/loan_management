from frappe import _

def get_data():
	return {
		'fieldname': 'customer',
		'non_standard_fieldnames': {
			'Journal Entry': 'reference_name',
			},
		'transactions': [
			{
				'label': _('Customer'),
				'items': ['Customer Loan Application']
			},
			{
				'label': _('Account'),
				'items': ['Journal Entry']
			}
		]
	}