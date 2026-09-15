# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestBeneficialOwner(TransactionCase):
    """TC-SEC-STAT-003: beneficial-owner nature_of_control validation and provisional flag."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test BO'})
        self.company = self.env.company

    def test_beneficial_owner_creation(self):
        """Basic beneficial owner creation works."""
        bo = self.env['govoo.register.beneficial.owner'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'nature_of_control': 'shares_25',
            'date_became_registrable': '2024-01-01',
        })
        self.assertEqual(bo.nature_of_control, 'shares_25')
        self.assertTrue(bo.is_provisional)

    def test_beneficial_owner_provisional_flag(self):
        """TC-SEC-STAT-003 / TC-ACC-003: Record flagged provisional for
        unconfirmed categories; no specific percentage/category is
        presented as authoritative before confirmation."""
        for category in ['shares_25', 'voting_25', 'board_appoint', 'significant']:
            bo = self.env['govoo.register.beneficial.owner'].create({
                'partner_id': self.partner.id,
                'company_id': self.company.id,
                'nature_of_control': category,
            })
            self.assertTrue(bo.is_provisional, f'{category} should be provisional')

    def test_charge_not_deletable(self):
        """TC-SEC-STAT-004: Charges cannot be deleted (BR-SEC-STAT-004)."""
        charge = self.env['govoo.register.charge'].create({
            'company_id': self.company.id,
            'amount': 1000000,
            'date_created': '2024-01-01',
        })
        with self.assertRaises(ValidationError):
            charge.unlink()

    def test_charge_marked_satisfied(self):
        """TC-SEC-STAT-004: Charge marked satisfied is still present."""
        charge = self.env['govoo.register.charge'].create({
            'company_id': self.company.id,
            'amount': 500000,
            'date_created': '2024-01-01',
        })
        charge.satisfied = True
        self.assertTrue(charge.satisfied)
        self.assertTrue(charge.exists(), 'Satisfied charge should still exist')

    def test_charge_amount_must_be_positive(self):
        """Charge amount must be > 0."""
        with self.assertRaises(ValidationError):
            self.env['govoo.register.charge'].create({
                'company_id': self.company.id,
                'amount': -100,
                'date_created': '2024-01-01',
            })

    def test_admin_and_auditor_cannot_read_other_company_beneficial_owner(self):
        """Admin/Auditor have CSV read access but must still be scoped to
        their own company on the single most sensitive register."""
        other_company = self.env['res.company'].create({'name': 'Other Company'})
        other_bo = self.env['govoo.register.beneficial.owner'].create({
            'partner_id': self.partner.id,
            'company_id': other_company.id,
            'nature_of_control': 'shares_25',
        })

        admin = new_test_user(
            self.env, login='test_bo_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        auditor = new_test_user(
            self.env, login='test_bo_auditor',
            groups='govoo_base.group_govoo_auditor',
            company_id=self.company.id,
        )

        for user in (admin, auditor):
            bos = self.env['govoo.register.beneficial.owner'].with_user(user).search([])
            self.assertNotIn(other_bo, bos)
            with self.assertRaises(AccessError):
                other_bo.with_user(user).check_access('read')
