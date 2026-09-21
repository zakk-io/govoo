# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestPortalAccess(GovooContractsTestBase):
    """Portal Access / Contract Viewer Portal (issue #177): BR-CM-007.

    Resolves the previously-open "named approver" data-model gap
    (docs/spec/decisions/assumptions.md) via the new
    portal_approver_ids field, rather than assuming it always equals
    counterparty_id.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.counterparty_partner = cls.counterparty
        cls.named_approver_partner = cls.env['res.partner'].create({
            'name': 'Named Approver Partner',
            'company_id': cls.company.id,
        })
        cls.outsider_partner = cls.env['res.partner'].create({
            'name': 'Unrelated Partner',
            'company_id': cls.company.id,
        })
        cls.counterparty_portal_user = new_test_user(
            cls.env, login='test_counterparty_portal',
            groups='govoo_base.group_govoo_contract_portal',
            company_id=cls.company.id,
            partner_id=cls.counterparty_partner.id,
        )
        cls.approver_portal_user = new_test_user(
            cls.env, login='test_named_approver_portal',
            groups='govoo_base.group_govoo_contract_portal',
            company_id=cls.company.id,
            partner_id=cls.named_approver_partner.id,
        )
        cls.outsider_portal_user = new_test_user(
            cls.env, login='test_outsider_portal',
            groups='govoo_base.group_govoo_contract_portal',
            company_id=cls.company.id,
            partner_id=cls.outsider_partner.id,
        )

    def test_counterparty_can_read_own_contract(self):
        contract = self._make_contract()
        contracts = self.env['govoo.contract'].with_user(
            self.counterparty_portal_user,
        ).search([])
        self.assertIn(contract, contracts)

    def test_named_approver_can_read_contract(self):
        contract = self._make_contract(portal_approver_ids=[(4, self.named_approver_partner.id)])
        contracts = self.env['govoo.contract'].with_user(
            self.approver_portal_user,
        ).search([])
        self.assertIn(contract, contracts)

    def test_outsider_cannot_read_contract(self):
        contract = self._make_contract(portal_approver_ids=[(4, self.named_approver_partner.id)])
        contracts = self.env['govoo.contract'].with_user(
            self.outsider_portal_user,
        ).search([])
        self.assertNotIn(contract, contracts)

    def test_outsider_cannot_browse_contract_by_id(self):
        """TC-SEC-010: direct/guessed-ID access denied at the record-rule
        level, not merely absent from the list."""
        contract = self._make_contract()
        contract_as_outsider = contract.with_user(self.outsider_portal_user)
        with self.assertRaises(AccessError):
            contract_as_outsider.check_access('read')

    def test_counterparty_cannot_write(self):
        contract = self._make_contract()
        with self.assertRaises(AccessError):
            contract.with_user(self.counterparty_portal_user).write({'value': 1.0})
