# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestGovooFeatureFlags(TransactionCase):
    """Issue #47: shared runtime detection for optional Documents/Sign apps."""

    def test_documents_app_not_installed_on_community(self):
        installed = self.env['ir.module.module'].search_count([
            ('name', '=', 'documents'),
            ('state', '=', 'installed'),
        ])
        self.assertEqual(
            self.env['govoo.feature.flags'].is_documents_app_installed(),
            bool(installed),
        )

    def test_sign_app_not_installed_on_community(self):
        installed = self.env['ir.module.module'].search_count([
            ('name', '=', 'sign'),
            ('state', '=', 'installed'),
        ])
        self.assertEqual(
            self.env['govoo.feature.flags'].is_sign_app_installed(),
            bool(installed),
        )
