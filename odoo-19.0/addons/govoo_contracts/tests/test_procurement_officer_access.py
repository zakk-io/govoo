# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install', 'govoo_contracts')
class TestProcurementOfficerContractAccess(GovooContractsTestBase):
    """Issue #352: the Procurement Officer can read (never write) the
    contract that resulted from a tender, but not the general contracts
    register. Confirms govoo_contract_comp_rule's own conditional
    narrowing actually holds rather than being silently widened back to
    full company scope by Odoo OR-combining it with the Officer's other
    group-scoped rules (every Officer also holds group_govoo_user)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.officer = new_test_user(
            cls.env, login='test_procurement_officer_contracts',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=cls.company.id,
        )
    def test_officer_can_read_contract_linked_to_a_tender(self):
        # #330's own gate requires both evaluations approved before a
        # contract can even link to a tender -- reuse the same helper
        # test_tender_link.py already built for exactly this.
        tender = self._make_evaluation_ready_tender()
        contract = self._make_contract(tender_id=tender.id)
        contract.with_user(self.officer).check_access('read')

    def test_officer_cannot_read_contract_without_a_tender(self):
        """The general contracts register (no tender_id) stays out of
        scope -- the Officer's grant is narrowed to procurement-
        originated contracts only, not every contract in the company."""
        contract = self._make_contract()
        with self.assertRaises(AccessError):
            contract.with_user(self.officer).check_access('read')

    def test_officer_cannot_write(self):
        tender = self._make_evaluation_ready_tender()
        contract = self._make_contract(tender_id=tender.id)
        with self.assertRaises(AccessError):
            contract.with_user(self.officer).write({'value': 1.0})

    def test_officer_with_broader_contract_role_is_not_narrowed(self):
        """An Officer who also holds a broader contract role (e.g.
        Contract Manager) must keep that role's own, broader access --
        the narrowing is specifically exempted for this case."""
        dual_role_user = new_test_user(
            self.env, login='test_officer_and_contract_manager',
            groups='govoo_procurement.group_govoo_procurement_officer,'
                   'govoo_base.group_govoo_contract_manager',
            company_id=self.company.id,
        )
        contract = self._make_contract()
        contract.with_user(dual_role_user).check_access('read')
