# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResCompanyGovernanceView(TransactionCase):
    """govoo_base.md: the Governance section must not hardcode fields as
    editable -- readonly must follow Odoo's default ACL-driven behavior
    (Board Administrator / Company Secretary write, read-only otherwise)."""

    def test_governance_fields_do_not_hardcode_readonly_zero(self):
        arch = self.env['res.company'].get_view(
            view_id=self.env.ref('base.view_company_form').id,
            view_type='form',
        )['arch']
        self.assertNotIn(
            'readonly="0"', arch,
            'Governance section fields must not hardcode readonly="0", '
            'which overrides Odoo\'s permission-driven readonly behavior.',
        )
