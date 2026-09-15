# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestGovooCommittee(TransactionCase):
    """TC-BASE-004: Committee membership resolves; cycle rejected."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company

    def test_committee_creation(self):
        """TC-BASE-004: Basic committee creation works."""
        committee = self.env['govoo.committee'].create({
            'name': 'Audit Committee',
            'company_id': self.company.id,
        })
        self.assertEqual(committee.name, 'Audit Committee')
        self.assertEqual(committee.company_id, self.company)

    def test_committee_parent_same_company(self):
        """TC-BASE-004: Parent committee must be same company."""
        other_company = self.env['res.company'].create({
            'name': 'Other Company',
        })
        parent = self.env['govoo.committee'].create({
            'name': 'Board',
            'company_id': self.company.id,
        })
        with self.assertRaises(ValidationError):
            self.env['govoo.committee'].create({
                'name': 'Sub Committee',
                'company_id': other_company.id,
                'parent_committee_id': parent.id,
            })

    def test_committee_self_parent_rejected(self):
        """TC-BASE-004: Committee cannot be its own parent."""
        committee = self.env['govoo.committee'].create({
            'name': 'Self Referential',
            'company_id': self.company.id,
        })
        with self.assertRaises(ValidationError):
            committee.write({'parent_committee_id': committee.id})

    def test_committee_cycle_detection(self):
        """TC-BASE-004: Cycle in committee hierarchy is rejected."""
        committee_a = self.env['govoo.committee'].create({
            'name': 'Committee A',
            'company_id': self.company.id,
        })
        committee_b = self.env['govoo.committee'].create({
            'name': 'Committee B',
            'company_id': self.company.id,
            'parent_committee_id': committee_a.id,
        })
        with self.assertRaises(ValidationError):
            committee_a.write({'parent_committee_id': committee_b.id})

    def test_committee_members_resolve_from_appointments(self):
        """TC-BASE-004: Members resolve from govoo.appointment records."""
        committee = self.env['govoo.committee'].create({
            'name': 'Finance Committee',
            'company_id': self.company.id,
        })
        partner = self.env['res.partner'].create({'name': 'Member 1'})
        self.env['govoo.appointment'].create({
            'partner_id': partner.id,
            'company_id': self.company.id,
            'role': 'committee_member',
            'committee_id': committee.id,
            'date_appointed': '2024-01-01',
        })
        self.assertEqual(len(committee.member_ids), 1)
        self.assertEqual(committee.member_ids.partner_id, partner)

    def test_admin_cannot_create_or_delete_committee(self):
        """access-control.md: Board Administrator gets RW on committee, not C/D."""
        admin = new_test_user(
            self.env, login='test_committee_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        committee = self.env['govoo.committee'].create({
            'name': 'Existing Committee',
            'company_id': self.company.id,
        })
        committee.with_user(admin).write({'name': 'Renamed by Admin'})
        with self.assertRaises(AccessError):
            self.env['govoo.committee'].with_user(admin).create({
                'name': 'New Committee',
                'company_id': self.company.id,
            })
        with self.assertRaises(AccessError):
            committee.with_user(admin).unlink()
