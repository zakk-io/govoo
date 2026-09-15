# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'govoo_rw')
class TestGovernanceChecklistItem(TransactionCase):
    """FR-RW-004: CMA Corporate Governance Code self-assessment checklist."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        obligation = cls.env.ref('govoo_rw.obligation_cma_governance_self_assessment')
        cls.instance = cls.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': cls.company.id,
            'due_date': '2026-12-31',
        })

    def test_checklist_item_creation(self):
        """TC-RW-004: checklist item created against a CMA governance
        self-assessment instance persists correctly."""
        item = self.env['govoo.rw.governance.checklist.item'].create({
            'instance_id': self.instance.id,
            'provision_ref': 'Principle 1',
            'status': 'comply',
        })
        self.assertEqual(item.company_id, self.company)

    def test_explanation_required_when_status_explain(self):
        with self.assertRaises(ValidationError):
            self.env['govoo.rw.governance.checklist.item'].create({
                'instance_id': self.instance.id,
                'provision_ref': 'Principle 2',
                'status': 'explain',
            })

    def test_explanation_provided_allows_explain_status(self):
        item = self.env['govoo.rw.governance.checklist.item'].create({
            'instance_id': self.instance.id,
            'provision_ref': 'Principle 3',
            'status': 'explain',
            'explanation': 'Not yet implemented pending board approval.',
        })
        self.assertEqual(item.status, 'explain')
