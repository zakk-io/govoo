# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestCommitteePortalAccess(GovooProcurementTestBase):
    """Issue #333: an external/extra Procurement Committee member gets
    read-only, committee-scoped access to the tender(s) their committee
    is evaluating -- same record-rule mechanism already proven for
    Director Portal access in govoo_board (committee_id.member_ids.
    partner_id = user.partner_id.id), reused here rather than reinvented."""

    def _make_committee_portal_user(self, login):
        return new_test_user(
            self.env, login=login,
            groups='govoo_procurement.group_govoo_procurement_committee_portal',
            company_id=self.company.id,
        )

    def _appoint_to_committee(self, partner, committee):
        return self.env['govoo.appointment'].create({
            'partner_id': partner.id,
            'committee_id': committee.id,
            'role': 'committee_member',
            'company_id': self.company.id,
            'date_appointed': '2026-01-01',
        })

    def test_committee_member_can_read_own_tender_and_bids(self):
        member = self._make_committee_portal_user('test_committee_portal_member')
        self._appoint_to_committee(member.partner_id, self.committee)
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        meeting = self._make_committee_meeting()
        tender.technical_evaluation_meeting_id = meeting.id

        tender.with_user(member).check_access('read')
        bid.with_user(member).check_access('read')

    def test_committee_member_cannot_read_unrelated_tender(self):
        member = self._make_committee_portal_user('test_committee_portal_other')
        self._appoint_to_committee(member.partner_id, self.committee)

        other_committee = self.env['govoo.committee'].create({
            'name': 'Unrelated Committee',
            'company_id': self.company.id,
        })
        other_meeting = self.env['govoo.meeting'].create({
            'name': 'Unrelated Meeting',
            'meeting_type': 'committee',
            'committee_id': other_committee.id,
            'date': '2026-05-01 10:00:00',
            'company_id': self.company.id,
        })
        other_tender = self._make_tender()
        other_tender.technical_evaluation_meeting_id = other_meeting.id
        other_bid = self._make_bid(other_tender, self.vendor_a)

        with self.assertRaises(AccessError):
            other_tender.with_user(member).check_access('read')
        with self.assertRaises(AccessError):
            other_bid.with_user(member).check_access('read')

    def test_non_member_cannot_read_any_tender(self):
        """A portal user holding the group but never appointed to any
        committee sees nothing -- membership, not the group alone, is
        what grants visibility."""
        non_member = self._make_committee_portal_user('test_committee_portal_non_member')
        tender = self._make_tender()
        meeting = self._make_committee_meeting()
        tender.technical_evaluation_meeting_id = meeting.id

        with self.assertRaises(AccessError):
            tender.with_user(non_member).check_access('read')

    def test_access_drops_once_appointment_is_inactive(self):
        member = self._make_committee_portal_user('test_committee_portal_resigned')
        appointment = self._appoint_to_committee(member.partner_id, self.committee)
        tender = self._make_tender()
        meeting = self._make_committee_meeting()
        tender.technical_evaluation_meeting_id = meeting.id

        tender.with_user(member).check_access('read')

        # date_resigned is the real field; state is computed from it.
        appointment.write({'date_resigned': '2026-02-01'})
        self.assertEqual(appointment.state, 'resigned')
        with self.assertRaises(AccessError):
            tender.with_user(member).check_access('read')

    def test_committee_member_cannot_write(self):
        member = self._make_committee_portal_user('test_committee_portal_readonly')
        self._appoint_to_committee(member.partner_id, self.committee)
        tender = self._make_tender()
        meeting = self._make_committee_meeting()
        tender.technical_evaluation_meeting_id = meeting.id

        with self.assertRaises(AccessError):
            tender.with_user(member).write({'name': 'Renamed'})
