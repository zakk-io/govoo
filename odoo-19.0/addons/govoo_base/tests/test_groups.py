# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

SPEC_GROUP_XML_IDS = [
    'govoo_base.group_govoo_user',
    'govoo_base.group_govoo_secretary',
    'govoo_base.group_govoo_admin',
    'govoo_base.group_govoo_director_portal',
    'govoo_base.group_govoo_shareholder_portal',
    'govoo_base.group_govoo_auditor',
]


@tagged('post_install', '-at_install')
class TestGovooGroups(TransactionCase):
    """TC-SEC-001: all six security groups exist with the specified XML IDs."""

    def test_all_six_groups_exist(self):
        for xml_id in SPEC_GROUP_XML_IDS:
            group = self.env.ref(xml_id, raise_if_not_found=False)
            self.assertTrue(group, f'Group {xml_id} should exist.')
            self.assertEqual(group._name, 'res.groups')
