# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestEndToEndBoardApprovalDemo(GovooContractsTestBase):
    """End-to-end regression test mirroring the manual demo walkthrough:
    generate a contract from a template, submit it, create a standalone
    board resolution (no meeting_id) and pass it by vote, link it to the
    contract, approve as a Contract Approver, execute within delegated
    authority, and activate.

    Unlike the narrower unit tests elsewhere in this suite (which fabricate
    a "passed" resolution via `resolution.write({'state': 'passed'})` and
    run under the test framework's superuser), this test drives every step
    through real non-superuser users and their actual action_* methods --
    the same combination (a standalone resolution created by a non-admin
    user) that surfaced the govoo.resolution.company_id bug fixed by PR
    #195 (a plain related field on meeting_id.company_id left company_id
    False whenever meeting_id was blank, which the multi-company ir.rule
    then rejected for every user with no group able to fix it)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.contract_type.approval_threshold = 60000000.0
        cls.clause = cls.env['govoo.contract.clause'].create({
            'name': 'Confidentiality',
            'company_id': cls.company.id,
            'is_mandatory': True,
        })
        cls.template = cls.env['govoo.contract.template'].create({
            'name': 'Consulting Services Template',
            'company_id': cls.company.id,
            'contract_type_id': cls.contract_type.id,
            'language': 'en',
            'clause_ids': [(6, 0, [cls.clause.id])],
        })
        cls.secretary = new_test_user(
            cls.env, login='test_secretary_e2e_demo',
            groups='govoo_base.group_govoo_secretary,'
                   'govoo_base.group_govoo_contract_manager',
            company_id=cls.company.id,
        )
        cls.approver = new_test_user(
            cls.env, login='test_approver_e2e_demo',
            groups='govoo_base.group_govoo_contract_approver',
            company_id=cls.company.id,
        )
        cls.env['govoo.contract.delegation'].create({
            'company_id': cls.company.id,
            'user_id': cls.approver.id,
            'max_value': 60000000.0,
        })
        cls.director = cls.env['res.partner'].create({
            'name': 'Robert Nkurunziza',
            'company_id': cls.company.id,
        })

    def test_full_lifecycle_via_generate_wizard_and_standalone_resolution(self):
        # 1. Generate the contract from a template (as Contract Manager).
        wizard = self.env['govoo.contract.generate.wizard'].with_user(
            self.secretary,
        ).create({
            'template_id': self.template.id,
            'counterparty_id': self.counterparty.id,
        })
        action = wizard.action_generate()
        contract = self.env['govoo.contract'].browse(
            action['res_id'],
        ).with_user(self.secretary)
        self.assertEqual(contract.state, 'draft')
        self.assertEqual(contract.template_id, self.template)

        # 2. Set the value at the type's approval threshold and submit.
        contract.value = 60000000.0
        contract.action_submit()
        self.assertEqual(contract.state, 'in_approval')

        # 3. Standalone board resolution -- no meeting_id -- opened, voted
        # on, and tallied to Passed, created by the Company Secretary.
        resolution = self.env['govoo.resolution'].with_user(
            self.secretary,
        ).create({
            'title': 'Approve Consulting Services Agreement with %s '
                     '(RWF 60,000,000)' % self.counterparty.name,
            'resolution_type': 'ordinary',
        })
        self.assertEqual(resolution.company_id, self.company)
        resolution.action_open()
        self.env['govoo.vote'].with_user(self.secretary).create({
            'resolution_id': resolution.id,
            'voter_id': self.director.id,
            'choice': 'for',
        })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')

        # 4. Link the resolution and approve (as Contract Approver).
        contract.resolution_id = resolution
        contract.with_user(self.approver).action_approve()
        self.assertEqual(contract.state, 'approved')

        # 5. Execute within delegated authority, then activate.
        contract.with_user(self.approver).action_execute()
        self.assertEqual(contract.state, 'executed')
        contract.with_user(self.approver).action_activate()
        self.assertEqual(contract.state, 'active')
