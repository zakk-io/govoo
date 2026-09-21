# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestTemplateClauseLibrary(GovooContractsTestBase):
    """Template/Clause Library & Generation (issue #168): TC-CM-009."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mandatory_clause = cls.env['govoo.contract.clause'].create({
            'name': 'Confidentiality',
            'company_id': cls.company.id,
            'is_mandatory': True,
            'clause_category': 'standard',
        })
        cls.optional_clause_a = cls.env['govoo.contract.clause'].create({
            'name': 'Exclusivity',
            'company_id': cls.company.id,
            'is_mandatory': False,
            'clause_category': 'optional',
        })
        cls.optional_clause_b = cls.env['govoo.contract.clause'].create({
            'name': 'Non-Compete',
            'company_id': cls.company.id,
            'is_mandatory': False,
            'clause_category': 'optional',
        })
        cls.template = cls.env['govoo.contract.template'].create({
            'name': 'Standard Supply Template',
            'company_id': cls.company.id,
            'contract_type_id': cls.contract_type.id,
            'language': 'en',
            'clause_ids': [(6, 0, [
                cls.mandatory_clause.id,
                cls.optional_clause_a.id,
                cls.optional_clause_b.id,
            ])],
        })

    def test_generate_includes_mandatory_clause_only_by_default(self):
        action = self.template.action_generate_contract(self.counterparty.id)
        contract = self.env['govoo.contract'].browse(action['res_id'])
        self.assertIn(self.mandatory_clause, contract.clause_ids)
        self.assertNotIn(self.optional_clause_a, contract.clause_ids)
        self.assertNotIn(self.optional_clause_b, contract.clause_ids)

    def test_generate_includes_selected_optional_clauses(self):
        action = self.template.action_generate_contract(
            self.counterparty.id, [self.optional_clause_a.id],
        )
        contract = self.env['govoo.contract'].browse(action['res_id'])
        self.assertIn(self.mandatory_clause, contract.clause_ids)
        self.assertIn(self.optional_clause_a, contract.clause_ids)
        self.assertNotIn(self.optional_clause_b, contract.clause_ids)

    def test_generate_ignores_unrelated_optional_clause_id(self):
        """An optional clause that doesn't belong to this template must
        never be pulled in, even if its id is passed."""
        other_clause = self.env['govoo.contract.clause'].create({
            'name': 'Unrelated Clause',
            'company_id': self.company.id,
            'is_mandatory': False,
        })
        action = self.template.action_generate_contract(
            self.counterparty.id, [other_clause.id],
        )
        contract = self.env['govoo.contract'].browse(action['res_id'])
        self.assertNotIn(other_clause, contract.clause_ids)

    def test_generated_contract_is_draft_and_linked_to_template(self):
        action = self.template.action_generate_contract(self.counterparty.id)
        contract = self.env['govoo.contract'].browse(action['res_id'])
        self.assertEqual(contract.state, 'draft')
        self.assertEqual(contract.template_id, self.template)
        self.assertEqual(contract.contract_type_id, self.contract_type)
        self.assertEqual(contract.counterparty_id, self.counterparty)

    def test_report_renders(self):
        """A minimal render-doesn't-crash check, same spirit as the
        report tests elsewhere in this codebase."""
        action = self.template.action_generate_contract(
            self.counterparty.id, [self.optional_clause_a.id],
        )
        contract = self.env['govoo.contract'].browse(action['res_id'])
        content, _report_type = self.env['ir.actions.report']._render_qweb_pdf(
            'govoo_contracts.action_report_govoo_contract', contract.ids,
        )
        self.assertTrue(content)
