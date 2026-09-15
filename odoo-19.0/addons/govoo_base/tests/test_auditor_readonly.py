# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestAuditorReadOnly(TransactionCase):
    """TC-SEC-007: Auditor is denied create/write/unlink at the
    access-rights layer on any governance model -- global read, no write.
    Representative sample across modules, not exhaustive."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.auditor = new_test_user(
            cls.env, login='test_readonly_auditor',
            groups='govoo_base.group_govoo_auditor',
            company_id=cls.company.id,
        )

    def test_auditor_cannot_write_committee(self):
        committee = self.env['govoo.committee'].create({
            'name': 'Auditor Test Committee',
            'company_id': self.company.id,
        })
        with self.assertRaises(AccessError):
            committee.with_user(self.auditor).write({'name': 'Tampered'})

    def test_auditor_cannot_create_committee(self):
        with self.assertRaises(AccessError):
            self.env['govoo.committee'].with_user(self.auditor).create({
                'name': 'New Committee',
                'company_id': self.company.id,
            })

    def test_auditor_cannot_unlink_appointment(self):
        partner = self.env['res.partner'].create({'name': 'Auditor Test Person'})
        appointment = self.env['govoo.appointment'].create({
            'partner_id': partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        with self.assertRaises(AccessError):
            appointment.with_user(self.auditor).unlink()

    def test_auditor_cannot_write_meeting(self):
        if 'govoo.meeting' not in self.env:
            self.skipTest('govoo_board not installed')
        committee = self.env['govoo.committee'].create({
            'name': 'Auditor Meeting Committee',
            'company_id': self.company.id,
        })
        meeting = self.env['govoo.meeting'].create({
            'name': 'Auditor Test Meeting',
            'committee_id': committee.id,
            'meeting_type': 'committee',
            'date': '2026-01-01 10:00:00',
            'company_id': self.company.id,
        })
        with self.assertRaises(AccessError):
            meeting.with_user(self.auditor).write({'name': 'Tampered'})
