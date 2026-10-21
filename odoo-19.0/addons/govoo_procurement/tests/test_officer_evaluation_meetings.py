# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestOfficerEvaluationMeetings(GovooProcurementTestBase):
    """Issue #357: the Procurement Officer can create/manage any
    committee-type meeting, but may only draft agenda/minutes for the
    Financial Evaluation meeting specifically, never Technical. Also
    confirms the narrowing doesn't silently take away the Officer's
    existing company-wide READ access to meetings/minutes (the same
    class of mistake #352's own write-up on ir.rule's OR-combination
    documents, here guarded against via perm_read=False instead)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.officer = new_test_user(
            cls.env, login='test_officer_evaluation_meetings',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=cls.company.id,
        )

    def _make_tender_with_both_meetings(self):
        tender = self._make_tender()
        technical = self._make_committee_meeting()
        financial = self._make_committee_meeting()
        tender.write({
            'technical_evaluation_meeting_id': technical.id,
            'financial_evaluation_meeting_id': financial.id,
        })
        return tender, technical, financial

    def test_officer_can_create_a_committee_meeting(self):
        meeting = self.env['govoo.meeting'].with_user(self.officer).create({
            'name': 'Technical Evaluation Meeting',
            'meeting_type': 'committee',
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'company_id': self.company.id,
        })
        self.assertTrue(meeting.id)

    def test_officer_cannot_create_a_board_meeting(self):
        with self.assertRaises(AccessError):
            self.env['govoo.meeting'].with_user(self.officer).create({
                'name': 'Board Meeting',
                'meeting_type': 'board',
                'committee_id': self.committee.id,
                'date': '2026-04-01 10:00:00',
                'company_id': self.company.id,
            })

    def test_evaluation_phase_synced_on_tender_write(self):
        tender, technical, financial = self._make_tender_with_both_meetings()
        self.assertEqual(technical.evaluation_phase, 'technical')
        self.assertEqual(financial.evaluation_phase, 'financial')

    def test_officer_can_draft_minutes_for_financial_evaluation_meeting(self):
        tender, technical, financial = self._make_tender_with_both_meetings()
        minutes = financial.with_user(self.officer).action_create_minutes()
        self.assertTrue(minutes)
        financial.invalidate_recordset()
        self.assertTrue(financial.minutes_id)

    def test_officer_cannot_draft_minutes_for_technical_evaluation_meeting(self):
        tender, technical, financial = self._make_tender_with_both_meetings()
        with self.assertRaises(AccessError):
            self.env['govoo.minutes'].with_user(self.officer).create({
                'meeting_id': technical.id,
            })

    def test_officer_can_add_agenda_item_to_financial_evaluation_meeting(self):
        tender, technical, financial = self._make_tender_with_both_meetings()
        item = self.env['govoo.agenda.item'].with_user(self.officer).create({
            'meeting_id': financial.id,
            'title': 'Review financial scores',
            'sequence': 1,
            'item_type': 'discussion',
        })
        self.assertTrue(item.id)

    def test_officer_cannot_add_agenda_item_to_technical_evaluation_meeting(self):
        tender, technical, financial = self._make_tender_with_both_meetings()
        with self.assertRaises(AccessError):
            self.env['govoo.agenda.item'].with_user(self.officer).create({
                'meeting_id': technical.id,
                'title': 'Review technical scores',
                'sequence': 1,
                'item_type': 'discussion',
            })

    def test_officer_read_access_to_meetings_and_minutes_not_narrowed(self):
        """A plain Board meeting the Officer has nothing to do with --
        read access must stay exactly as broad as it was before this
        role gained write/create on committee meetings."""
        board_meeting = self.env['govoo.meeting'].create({
            'name': 'Board Meeting',
            'meeting_type': 'board',
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'company_id': self.company.id,
        })
        board_meeting.with_user(self.officer).check_access('read')
        minutes = self.env['govoo.minutes'].create({'meeting_id': board_meeting.id})
        minutes.with_user(self.officer).check_access('read')

    def test_officer_cannot_write_a_board_meeting(self):
        board_meeting = self.env['govoo.meeting'].create({
            'name': 'Board Meeting',
            'meeting_type': 'board',
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'company_id': self.company.id,
        })
        with self.assertRaises(AccessError):
            board_meeting.with_user(self.officer).write({'name': 'Hacked'})

    def test_secretary_role_not_narrowed_by_officer_rule(self):
        """A dual-role user (Officer + Secretary) keeps Secretary's own
        broader access -- the narrowing is specifically exempted for
        this case, same precedent as #352/#354's own dual-role tests."""
        dual_role_user = new_test_user(
            self.env, login='test_officer_and_secretary',
            groups='govoo_procurement.group_govoo_procurement_officer,'
                   'govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        tender, technical, financial = self._make_tender_with_both_meetings()
        # Secretary can draft minutes for the Technical meeting too,
        # unlike a plain Officer.
        minutes = self.env['govoo.minutes'].with_user(dual_role_user).create({
            'meeting_id': technical.id,
        })
        self.assertTrue(minutes.id)
