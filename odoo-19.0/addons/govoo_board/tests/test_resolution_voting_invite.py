# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class TestResolutionVotingInvite(GovooBoardTestBase):
    """Resolution voting-invite emails (issue #234): action_open notifies
    eligible voters via the same two-channel pattern as board pack
    distribution (message_post + a real email), auto-granting portal
    access first (via Odoo's own "Grant Portal Access" flow) for anyone
    who doesn't have it yet but has a usable email -- only a voter with
    no usable email at all stays flagged instead."""

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
        # partner_b/c/d deliberately get no res.users record AND no email,
        # so auto-grant has nothing to work with and they stay flagged.

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

        # assertIn rather than exact-equality: this runs against the
        # shared dev company, which already has other real shareholders
        # on file -- this test only asserts our own fixture's voter row
        # is correct, not that it is the only eligible one.
        notif = resolution.voter_notification_ids.filtered(lambda v: v.partner_id == shareholder)
        self.assertTrue(notif)
        self.assertEqual(notif.voter_type, 'shareholder')
        self.assertTrue(notif.notified_date)

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

    def test_director_voter_without_access_gets_one_auto_created(self):
        """A voter with a usable email but no res.users yet is
        auto-granted portal access (via Odoo's own "Grant Portal Access"
        flow) rather than just being skipped."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self.partner_a.email = 'director.a@example.com'
        self.assertFalse(self.env['res.users'].search([('partner_id', '=', self.partner_a.id)]))

        resolution.action_open()

        notif_a = resolution.voter_notification_ids.filtered(lambda v: v.partner_id == self.partner_a)
        self.assertTrue(notif_a.has_portal_access)
        self.assertTrue(notif_a.notified_date)
        user = self.env['res.users'].search([('partner_id', '=', self.partner_a.id)])
        self.assertTrue(user)
        self.assertTrue(user.has_group('govoo_base.group_govoo_director_portal'))

    def test_shareholder_voter_auto_granted_gets_shareholder_group(self):
        """Same auto-grant, but a shareholder-type voter must land in the
        shareholder portal group, not the director one."""
        shareholder = self._make_shareholder('Auto Grant Shareholder', 300)
        shareholder.email = 'shareholder.autogrant@example.com'
        resolution = self.env['govoo.resolution'].create({
            'title': 'Written Resolution Auto Grant',
            'resolution_type': 'ordinary',
        })

        resolution.action_open()

        user = self.env['res.users'].search([('partner_id', '=', shareholder.id)])
        self.assertTrue(user)
        self.assertTrue(user.has_group('govoo_base.group_govoo_shareholder_portal'))

    def test_voter_without_any_email_is_still_flagged_not_auto_created(self):
        """No usable email means there's nothing to auto-grant with --
        this is the one remaining case that stays flagged."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self.assertFalse(self.partner_b.email)

        resolution.action_open()

        notif_b = resolution.voter_notification_ids.filtered(lambda v: v.partner_id == self.partner_b)
        self.assertFalse(notif_b.has_portal_access)
        self.assertFalse(self.env['res.users'].search([('partner_id', '=', self.partner_b.id)]))
        # All 4 directors (a/b/c/d) have no email in this test, unlike
        # test_voter_with_portal_access_is_emailed_and_voter_without_is_flagged
        # which gives partner_a access first -- so all 4 stay unreachable here.
        self.assertEqual(resolution.unreachable_voter_count, 4)

    def test_auto_granted_voter_also_receives_the_voting_invite_email(self):
        """Granting access and sending the voting-invite email both
        happen in the same action_open() call -- a newly-granted voter
        should not need a second action to get their link."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self.partner_a.email = 'director.a2@example.com'
        mail_count_before = self.env['mail.mail'].search_count([])

        resolution.action_open()

        mail_count_after = self.env['mail.mail'].search_count([])
        self.assertGreater(
            mail_count_after, mail_count_before,
            'Auto-granting access should not skip sending the actual voting-invite email.',
        )
        notif_a = resolution.voter_notification_ids.filtered(lambda v: v.partner_id == self.partner_a)
        self.assertTrue(notif_a.notified_date)
