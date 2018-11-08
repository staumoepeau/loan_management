frappe.listview_settings['Customer Loan Appliaction'] = {
  add_fields: ['disbursement_status', 'repayment_status'],
  get_indicator: function({ disbursement_status, repayment_status }) {
    if (docstatus == 1 && workflow_status == "Approved"){
      if (disbursement_status === 'Sanctioned') {
        return [__('Sanctioned'), 'darkgrey', 'disbursement_status,=,Sanctioned'];
      }
      if (disbursement_status === 'Partially Disbursed') {
        return [
          __('Pending'),
          'orange',
          'disbursement_status,=,Partially Disbursed',
        ];
      }
      if (
        disbursement_status === 'Fully Disbursed' &&
        repayment_status === 'Not Started'
      ) {
        return [
          __('Disbursed'),
          'yellow',
          'disbursement_status,=,Fully Disbursed|repayment_status,=,Not Started',
        ];
      }
      if (
        disbursement_status === 'Fully Disbursed' &&
        repayment_status === 'In Progress'
      ) {
        return [
          __('In Progress'),
          'lightblue',
          'disbursement_status,=,Fully Disbursed|repayment_status,=,In Progress',
        ];
      }
      if (
        disbursement_status === 'Fully Disbursed' &&
        repayment_status === 'Repaid'
      ) {
        return [
          __('Cleared'),
          'blue',
          'disbursement_status,=,Fully Disbursed|repayment_status,=,Repaid',
        ];
      }
    }
  },
};
