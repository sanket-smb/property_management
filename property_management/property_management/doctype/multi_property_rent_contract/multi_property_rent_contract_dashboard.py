from frappe import _

def get_data():
	return {
		'fieldname': 'multi_rent_contract_no',
		'transactions': [
			{
				'label': _('Rent Contract'),
				'items': ['Rent Contract']
			}
		]
	}