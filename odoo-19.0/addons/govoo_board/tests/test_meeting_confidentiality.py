# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestMeetingConfidentiality(GovooBoardTestBase):
    """Meeting Confidentiality Partitioning (issue #202): "executive" and
    "departmental" meetings are restricted to committee members (plus the
    Company Secretary, who organizes them); board/committee/agm/egm
    meetings remain visible to every internal governance user exactly as
    before -- no regression on the existing baseline."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.outsider = new_test_user(
            cls.env, login='test_meeting_outsider',
            groups='govoo_base.group_govoo_user',
            company_id=cls.company.id,
        )
        cls.secretary = new_test_user(
            cls.env, login='test_meeting_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=cls.company.id,
        )
        cls.member_user = new_test_user(
            cls.env, login='test_meeting_committee_member',
            groups='govoo_base.group_govoo_user',
            company_id=cls.company.id,
        )
        cls.env['govoo.appointment'].create({
            'partner_id': cls.member_user.partner_id.id,
            'company_id': cls.company.id,
            'role': 'director',
            'committee_id': cls.committee.id,
            'date_appointed': '2025-01-01',
        })

    def _make_confidential_meeting(self, meeting_type='executive'):
        return self.env['govoo.meeting'].create({
            'name': 'Executive Strategy Session',
            'meeting_type': meeting_type,
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'company_id': self.company.id,
        })

    def test_outsider_cannot_read_executive_meeting(self):
        meeting = self._make_confidential_meeting('executive')
        self.assertNotIn(
            meeting, self.env['govoo.meeting'].with_user(self.outsider).search([]),
        )

    def test_outsider_cannot_read_departmental_meeting(self):
        meeting = self._make_confidential_meeting('departmental')
        self.assertNotIn(
            meeting, self.env['govoo.meeting'].with_user(self.outsider).search([]),
        )

    def test_committee_member_can_read_executive_meeting(self):
        meeting = self._make_confidential_meeting('executive')
        self.assertIn(
            meeting, self.env['govoo.meeting'].with_user(self.member_user).search([]),
        )

    def test_secretary_can_always_read_executive_meeting(self):
        meeting = self._make_confidential_meeting('executive')
        self.assertIn(
            meeting, self.env['govoo.meeting'].with_user(self.secretary).search([]),
        )

    def test_outsider_can_still_read_board_meeting(self):
        """No regression: an ordinary board meeting stays visible to every
        internal governance user, exactly as before this issue."""
        meeting = self._make_meeting()
        self.assertIn(
            meeting, self.env['govoo.meeting'].with_user(self.outsider).search([]),
        )

    def test_outsider_cannot_read_agenda_item_of_executive_meeting(self):
        meeting = self._make_confidential_meeting('executive')
        agenda_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Confidential strategy item',
            'item_type': 'discussion',
        })
        self.assertNotIn(
            agenda_item,
            self.env['govoo.agenda.item'].with_user(self.outsider).search([]),
        )

    def test_committee_member_can_read_agenda_item_of_executive_meeting(self):
        meeting = self._make_confidential_meeting('executive')
        agenda_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Confidential strategy item',
            'item_type': 'discussion',
        })
        self.assertIn(
            agenda_item,
            self.env['govoo.agenda.item'].with_user(self.member_user).search([]),
        )

    def test_outsider_cannot_read_minutes_of_executive_meeting(self):
        meeting = self._make_confidential_meeting('executive')
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Confidential minutes.</p>',
        })
        self.assertNotIn(
            minutes, self.env['govoo.minutes'].with_user(self.outsider).search([]),
        )

    def test_committee_member_can_read_minutes_of_executive_meeting(self):
        meeting = self._make_confidential_meeting('executive')
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Confidential minutes.</p>',
        })
        self.assertIn(
            minutes, self.env['govoo.minutes'].with_user(self.member_user).search([]),
        )
