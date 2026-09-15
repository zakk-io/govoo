# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStatButtons(TransactionCase):
    """Test stat buttons and computed count fields across models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.committee = cls.env['govoo.committee'].create({
            'name': 'Test Committee',
            'company_id': cls.company.id,
        })

    def test_partner_appointment_count(self):
        """Partner appointment_count computes correctly."""
        self.assertEqual(self.partner.appointment_count, 0)
        self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        self.partner.invalidate_recordset(['appointment_count'])
        self.assertEqual(self.partner.appointment_count, 1)

    def test_partner_action_view_appointments(self):
        """action_view_appointments returns correct action."""
        action = self.partner.action_view_appointments()
        self.assertEqual(action['res_model'], 'govoo.appointment')
        self.assertEqual(action['domain'], [('partner_id', '=', self.partner.id)])

    def test_committee_member_count(self):
        """Committee member_count computes correctly."""
        self.assertEqual(self.committee.member_count, 0)
        self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'committee_id': self.committee.id,
            'date_appointed': '2024-01-01',
        })
        self.committee.invalidate_recordset(['member_count'])
        self.assertEqual(self.committee.member_count, 1)

    def test_committee_meeting_count(self):
        """Committee meeting_count computes correctly."""
        self.assertEqual(self.committee.meeting_count, 0)
        self.env['govoo.meeting'].create({
            'name': 'Test Meeting',
            'meeting_type': 'board',
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'quorum_required': 1,
            'attendee_ids': [(6, 0, [self.partner.id])],
            'company_id': self.company.id,
        })
        self.committee.invalidate_recordset(['meeting_count'])
        self.assertEqual(self.committee.meeting_count, 1)

    def test_committee_action_view_members(self):
        """action_view_members returns correct action."""
        action = self.committee.action_view_members()
        self.assertEqual(action['res_model'], 'govoo.appointment')
        self.assertEqual(action['domain'], [
            ('committee_id', '=', self.committee.id),
            ('role', '!=', 'secretary'),
            ('state', '=', 'active'),
        ])

    def test_committee_action_view_meetings(self):
        """action_view_meetings returns correct action."""
        action = self.committee.action_view_meetings()
        self.assertEqual(action['res_model'], 'govoo.meeting')
        self.assertEqual(action['domain'], [('committee_id', '=', self.committee.id)])
