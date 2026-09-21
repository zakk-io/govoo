# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestFinancialLinkage(GovooContractsTestBase):
    """Financial Linkage (issue #176, [OPTIONAL]/[CONFIRM]): BR-CM-008.

    Same pattern as govoo_shares' GL posting hook (BR-SHARE-004,
    TC-SHARE-005): the accounting policy is unconfirmed
    (docs/spec/decisions/open-decisions.md), so no GL-posting mechanism
    is built at all yet -- this test only proves the absence, matching
    govoo_shares' own test_no_gl_posting_by_default exactly. Building a
    disabled-by-default hook for a policy nobody has confirmed would be
    speculative code the addendum's own module DoD doesn't require
    (modules/govoo_contracts.md "Out of scope for this module").
    """

    def test_no_gl_posting_for_full_contract_lifecycle(self):
        account_installed = self.env['ir.module.module'].search_count([
            ('name', '=', 'account'),
            ('state', '=', 'installed'),
        ])
        if not account_installed:
            return

        self._grant_delegation()
        contract = self._make_contract()
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        contract.action_activate()

        moves = self.env['account.move'].search([
            ('ref', 'ilike', '%contract%'),
        ])
        self.assertFalse(moves)
