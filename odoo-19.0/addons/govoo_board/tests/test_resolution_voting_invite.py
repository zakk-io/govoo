# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class TestResolutionVotingInvite(GovooBoardTestBase):
    """Resolution voting-invite emails (issue #234): action_open notifies
    eligible voters via the same two-channel pattern as board pack
    distribution (message_post + a real email), skipping and flagging
    voters with no portal account rather than auto-provisioning one."""

    def _give_portal_access(self, partner, login, group_xmlid):
        return self.env['res.users'].create({
            'name': partner.name,
            'login': login,
            'partner_id': partner.id,
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'group_ids': [(6, 0, [self.env.ref(group_xmlid).id])],
        })

    def _make_shareholder(self, name, quantity):
        share_class = self.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000,
            'votes_per_share': 1.0,
            'total_authorised': 1000,
            'company_id': self.company.id,
        })
        partner = self.env['res.partner'].create({
            'name': name,
            'company_id': self.company.id,
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': partner.id,
            'quantity': quantity,
            'date_allotted': '2026-01-01',
        })
        return partner

    def test_action_open_notifies_directors_for_board_meeting_resolution(self):
        """A plain board-meeting resolution (meeting_type='board') is
        director-only -- no shareholder is eligible, matching
        govoo_vote.create()'s own gating."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self._give_portal_access(self.partner_a, 'test_voter_director_a', 'govoo_base.group_govoo_director_portal')

        resolution.action_open()

        self.assertEqual(
            set(resolution.voter_notification_ids.mapped('partner_id')),
            {self.partner_a, self.partner_b, self.partner_c, self.partner_d},
        )
        self.assertTrue(
            all(v == 'director' for v in resolution.voter_notification_ids.mapped('voter_type')),
        )

    def test_voter_with_portal_access_is_emailed_and_voter_without_is_flagged(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self._give_portal_access(self.partner_a, 'test_voter_with_access', 'govoo_base.group_govoo_director_portal')
        # partner_b/c/d deliberately get no res.users record.

        mail_count_before = self.env['mail.mail'].search_count([])
        resolution.action_open()
        mail_count_after = self.env['mail.mail'].search_count([])

        notif_a = resolution.voter_notification_ids.filtered(lambda v: v.partner_id == self.partner_a)
        notif_others = resolution.voter_notification_ids - notif_a
        self.assertTrue(notif_a.has_portal_access)
        self.assertTrue(notif_a.notified_date)
        self.assertTrue(all(not v.has_portal_access for v in notif_others))
        self.assertTrue(all(not v.notified_date for v in notif_others))
        self.assertGreater(
            mail_count_after, mail_count_before,
            'The reachable voter should still get a real voting-invite email.',
        )
        self.assertEqual(resolution.unreachable_voter_count, 3)

    def test_action_open_still_posts_in_app_notification(self):
        """No regression: the in-app chatter notification is sent
        alongside the email, not replaced by it (same two-channel
        guarantee as board pack distribution)."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self._give_portal_access(self.partner_a, 'test_voter_chatter', 'govoo_base.group_govoo_director_portal')
        message_count_before = len(resolution.message_ids)

        resolution.action_open()

        self.assertGreater(len(resolution.message_ids), message_count_before)

    def test_action_open_notifies_shareholders_for_written_ordinary_resolution(self):
        """A written resolution (no meeting_id) with resolution_type
        'ordinary' is shareholder-eligible, sourced from actual holdings
        -- not merely from resolution_type, unlike today's shareholder
        portal listing."""
        shareholder = self._make_shareholder('Shareholder With Holding', 500)
        self._give_portal_access(
            shareholder, 'test_voter_shareholder', 'govoo_base.group_govoo_shareholder_portal',
        )
        resolution = self.env['govoo.resolution'].create({
            'title': 'Written Resolution For Shareholders',
            'resolution_type': 'ordinary',
        })

        resolution.action_open()

        self.assertEqual(resolution.voter_notification_ids.partner_id, shareholder)
        self.assertEqual(resolution.voter_notification_ids.voter_type, 'shareholder')
        self.assertTrue(resolution.voter_notification_ids.notified_date)

    def test_director_and_shareholder_both_eligible_on_agm_resolution(self):
        """An AGM-linked ordinary resolution is eligible to both the
        committee's directors and the company's shareholders."""
        shareholder = self._make_shareholder('AGM Shareholder', 200)
        agm_meeting = self.env['govoo.meeting'].create({
            'name': 'Annual General Meeting',
            'meeting_type': 'agm',
            'committee_id': self.committee.id,
            'date': '2026-05-01 10:00:00',
            'quorum_required': 3,
            'attendee_ids': [(6, 0, [self.partner_a.id, self.partner_b.id])],
            'company_id': self.company.id,
        })
        resolution = self._make_resolution(agm_meeting)

        resolution.action_open()

        voter_partners = resolution.voter_notification_ids.mapped('partner_id')
        self.assertIn(shareholder, voter_partners)
        self.assertIn(self.partner_a, voter_partners)
        shareholder_notif = resolution.voter_notification_ids.filtered(
            lambda v: v.partner_id == shareholder,
        )
        director_notif = resolution.voter_notification_ids.filtered(
            lambda v: v.partner_id == self.partner_a,
        )
        self.assertEqual(shareholder_notif.voter_type, 'shareholder')
        self.assertEqual(director_notif.voter_type, 'director')

    def test_voting_link_differs_by_voter_type(self):
        """The emailed link routes directors and shareholders to their own
        distinct portal cast-vote route (issue #234's own fix for the
        single hardcoded director-only access_url)."""
        shareholder = self._make_shareholder('Link Check Shareholder', 100)
        resolution = self.env['govoo.resolution'].create({
            'title': 'Written Resolution Link Check',
            'resolution_type': 'ordinary',
        })
        resolution.action_open()

        notif = resolution.voter_notification_ids.filtered(lambda v: v.partner_id == shareholder)
        self.assertIn('/my/holdings/votes/', notif.portal_url)

        meeting = self._make_meeting()
        director_resolution = self._make_resolution(meeting)
        director_resolution.action_open()
        director_notif = director_resolution.voter_notification_ids.filtered(
            lambda v: v.partner_id == self.partner_a,
        )
        self.assertIn('/my/votes/', director_notif.portal_url)
        self.assertNotIn('/my/holdings/votes/', director_notif.portal_url)
