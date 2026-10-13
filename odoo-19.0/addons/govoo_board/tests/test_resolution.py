# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooResolutionTC(GovooBoardTestBase):
    """TC-BOARD-004, 005 — Resolution state machine and tally."""

    def test_resolution_state_machine(self):
        """draft → open → passed/failed."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self.assertEqual(resolution.state, 'draft')
        resolution.action_open()
        self.assertEqual(resolution.state, 'open')

    def test_resolution_invalid_transition_rejected(self):
        """Cannot skip from draft to passed via tally."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        with self.assertRaises(ValidationError):
            resolution.action_tally()

    def test_resolution_withdraw_from_draft(self):
        """Resolution can be withdrawn from draft."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_withdraw()
        self.assertEqual(resolution.state, 'withdrawn')

    def test_tally_passes_with_majority(self):
        """TC-BOARD-005 / TC-WF-BOARD-004: Resolution open, quorum met,
        majority achieved → passed."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        # Cast votes: 3 for, 1 against
        for partner in [self.partner_a, self.partner_b, self.partner_c]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_d.id,
            'choice': 'against',
        })

        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')
        self.assertEqual(resolution.result, 'passed')

    def test_tally_fails_without_majority(self):
        """Resolution with more against votes → failed."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        # Cast votes: 1 for, 3 against
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        for partner in [self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'against',
            })

        resolution.action_tally()
        self.assertEqual(resolution.state, 'failed')
        self.assertEqual(resolution.result, 'failed')

    def test_tally_on_non_open_rejected(self):
        """Can only tally an open resolution."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        # Still in draft
        with self.assertRaises(ValidationError):
            resolution.action_tally()

    def test_agenda_linked_resolution_meeting_mismatch_rejected(self):
        """Issue #82: a resolution linked via agenda_item_id must have a
        matching meeting_id, so it stays visible to
        meeting.resolution_ids (and action_close's terminal-state check)."""
        meeting = self._make_meeting()
        other_meeting = self._make_meeting()
        agenda_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Item',
            'item_type': 'decision',
        })
        with self.assertRaises(ValidationError):
            self.env['govoo.resolution'].create({
                'title': 'Mismatched Resolution',
                'resolution_type': 'ordinary',
                'agenda_item_id': agenda_item.id,
                'meeting_id': other_meeting.id,
            })

    def test_agenda_linked_resolution_blank_meeting_rejected(self):
        """Issue #82: agenda_item_id set with meeting_id left blank is
        also rejected (not just a mismatch)."""
        meeting = self._make_meeting()
        agenda_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Item',
            'item_type': 'decision',
        })
        with self.assertRaises(ValidationError):
            self.env['govoo.resolution'].create({
                'title': 'No Meeting Resolution',
                'resolution_type': 'ordinary',
                'agenda_item_id': agenda_item.id,
            })

    def test_action_close_blocked_by_agenda_linked_open_resolution(self):
        """Issue #82: action_close correctly blocks when an
        agenda-linked resolution (not directly meeting_id-linked at
        create time, but consistent per the new constraint) is still
        open."""
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()

        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        meeting.minutes_id = minutes
        meeting.action_minute()

        agenda_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Item',
            'item_type': 'decision',
        })
        resolution = self.env['govoo.resolution'].create({
            'title': 'Agenda-Linked Resolution',
            'resolution_type': 'ordinary',
            'agenda_item_id': agenda_item.id,
            'meeting_id': meeting.id,
        })
        resolution.action_open()

        self.assertIn(resolution, meeting.resolution_ids)
        with self.assertRaises(ValidationError):
            meeting.action_close()

    def test_tally_fails_when_quorum_not_met_despite_unanimous_votes(self):
        """BR-BOARD-005: quorum is a precondition for 'passed', independent
        of the vote tally -- unanimous votes on a meeting that never met
        quorum must still fail."""
        meeting = self._make_meeting(quorum=10)  # only 4 attendees -> never met
        self.assertFalse(meeting.quorum_met)
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'failed')
        self.assertEqual(resolution.result, 'failed')

    def test_special_resolution_tally_raises_without_configured_threshold(self):
        """A 'special' resolution cannot be tallied at all until the
        majority threshold is explicitly configured (no silent plain
        majority fallback)."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting, resolution_type='special')
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        with self.assertRaises(ValidationError):
            resolution.action_tally()

    def test_special_resolution_tally_uses_configured_threshold(self):
        """Once configured, a 'special' resolution passes/fails at the
        configured supermajority fraction rather than plain majority."""
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.special_resolution_majority_threshold', '0.75',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting, resolution_type='special')
        resolution.action_open()
        # 3 for, 1 against = 75% -- exactly clears a 0.75 threshold
        for partner in [self.partner_a, self.partner_b, self.partner_c]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_d.id,
            'choice': 'against',
        })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')

        # 2 for, 2 against = 50% -- does not clear 0.75
        meeting2 = self._make_meeting()
        resolution2 = self._make_resolution(meeting2, resolution_type='special')
        resolution2.action_open()
        for partner in [self.partner_a, self.partner_b]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution2.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        for partner in [self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution2.id,
                'voter_id': partner.id,
                'choice': 'against',
            })
        resolution2.action_tally()
        self.assertEqual(resolution2.state, 'failed')

    def test_sign_request_blocked_without_legal_confirmation(self):
        """BR-BOARD-008: sign_request_id cannot be set while e-signature
        legal validity under Rwandan law is unconfirmed (the default)."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        attachment = self.env['ir.attachment'].create({
            'name': 'sign_request.pdf',
            'datas': b'ZmFrZSBwZGY=',
        })
        with self.assertRaises(ValidationError):
            resolution.sign_request_id = attachment

    def test_tally_marks_vote_activity_done(self):
        """Issue #154: reaching a terminal state via action_tally() must
        clear the "Vote on resolution" activity scheduled by action_open(),
        not leave it nagging as overdue forever."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.assertTrue(
            resolution.activity_ids.filtered(
                lambda a: a.activity_type_id == self.env.ref('mail.mail_activity_data_todo'),
            ),
        )
        for partner in [self.partner_a, self.partner_b, self.partner_c]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')
        self.assertFalse(
            resolution.activity_ids.filtered(
                lambda a: a.activity_type_id == self.env.ref('mail.mail_activity_data_todo'),
            ),
        )

    def test_withdraw_marks_vote_activity_done(self):
        """Issue #154: withdrawing an open resolution must also clear the
        "Vote on resolution" activity."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        resolution.action_withdraw()
        self.assertEqual(resolution.state, 'withdrawn')
        self.assertFalse(
            resolution.activity_ids.filtered(
                lambda a: a.activity_type_id == self.env.ref('mail.mail_activity_data_todo'),
            ),
        )

    def test_standalone_written_resolution_gets_company_id(self):
        """Regression test: a written resolution with no meeting_id (nullable
        per docs/spec/modules/govoo_board.md) must still get a company_id,
        or the multi-company ir.rule (company_id in company_ids) blocks its
        creation for every user -- found manually in the UI as the Company
        Secretary: a generic "Access Error" naming no group to fix, because
        the failure was a record rule, not a missing ir.model.access row."""
        secretary = new_test_user(
            self.env, login='test_secretary_standalone_resolution',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        resolution = self.env['govoo.resolution'].with_user(secretary).create({
            'title': 'Written Resolution With No Meeting',
            'resolution_type': 'written',
        })
        self.assertEqual(resolution.company_id, self.company)

    def test_sign_request_allowed_when_legally_confirmed(self):
        """Once confirmed, sign_request_id can be set."""
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        attachment = self.env['ir.attachment'].create({
            'name': 'sign_request.pdf',
            'datas': b'ZmFrZSBwZGY=',
        })
        resolution.sign_request_id = attachment
        self.assertEqual(resolution.sign_request_id, attachment)

    # -- Issue #269 item 5: notice period --------------------------------

    def test_notice_period_unset_preserves_default_behavior(self):
        """Unset (default) notice period: open succeeds regardless of how
        close the meeting date is -- the exact behavior before this field
        existed."""
        meeting = self._make_meeting()  # default date is not "soon" from now
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.assertEqual(resolution.state, 'open')

    def test_notice_period_blocks_open_when_meeting_too_soon(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.resolution_notice_period_days', '14',
        )
        meeting = self._make_meeting()
        meeting.date = fields.Datetime.now() + timedelta(days=5)
        resolution = self._make_resolution(meeting)
        with self.assertRaises(ValidationError):
            resolution.action_open()

    def test_notice_period_allows_open_when_meeting_far_enough_out(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.resolution_notice_period_days', '14',
        )
        meeting = self._make_meeting()
        meeting.date = fields.Datetime.now() + timedelta(days=30)
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.assertEqual(resolution.state, 'open')

    # -- Issue #269 item 6: gate opening on meeting state ----------------

    def test_meeting_state_gate_disabled_by_default(self):
        """govoo.meeting defaults to 'draft', and this module's own test
        suite routinely opens resolutions against a draft meeting -- the
        gate must stay opt-in."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.assertEqual(resolution.state, 'open')

    def test_meeting_state_gate_blocks_draft_meeting_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.resolution_meeting_state_gate_enabled', 'True',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        with self.assertRaises(ValidationError):
            resolution.action_open()

    def test_meeting_state_gate_allows_scheduled_meeting_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.resolution_meeting_state_gate_enabled', 'True',
        )
        meeting = self._make_meeting()
        meeting.action_schedule()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.assertEqual(resolution.state, 'open')

    # -- Issue #269 item 4: tie-break / chair's casting vote -------------

    def test_tie_fails_by_default(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        for partner in [self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'against',
            })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'failed')
        self.assertFalse(resolution.tie_break_pending)

    def test_tie_break_enabled_waits_for_casting_vote(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.resolution_tie_break_enabled', 'True',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        for partner in [self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'against',
            })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'open')
        self.assertTrue(resolution.tie_break_pending)

        secretary = new_test_user(
            self.env, login='test_secretary_casting_vote',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        resolution.with_user(secretary).action_chair_casting_vote('passed')
        self.assertEqual(resolution.state, 'passed')
        self.assertEqual(resolution.result, 'passed')
        self.assertFalse(resolution.tie_break_pending)

    def test_casting_vote_restricted_to_secretary_or_admin(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.resolution_tie_break_enabled', 'True',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        for partner in [self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'against',
            })
        resolution.action_tally()
        self.assertTrue(resolution.tie_break_pending)

        plain_user = new_test_user(
            self.env, login='test_plain_user_casting_vote',
            groups='govoo_base.group_govoo_user',
            company_id=self.company.id,
        )
        with self.assertRaises(ValidationError):
            resolution.with_user(plain_user).action_chair_casting_vote('passed')

    # -- Issue #269 item 7: quorum for standalone resolutions ------------

    def _make_standalone_shareholder_resolution_with_holdings(self, quorum_percentage):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.written_resolution_quorum_percentage', str(quorum_percentage),
        )
        # _get_eligible_voters() searches ALL govoo.share.holding for the
        # resolution's company -- self.company is this project's shared,
        # heavily-seeded demo company, so a fresh company here isolates
        # the eligible-voter count to exactly the 4 holdings below instead
        # of also counting every other shareholder already seeded on
        # self.company.
        company = self.env['res.company'].create({'name': 'Quorum Test Co'})
        share_class = self.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000,
            'votes_per_share': 1.0,
            'total_authorised': 100,
            'company_id': company.id,
        })
        for partner in [self.partner_a, self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.share.allotment'].create({
                'share_class_id': share_class.id,
                'partner_id': partner.id,
                'quantity': 10,
                'date_allotted': '2026-01-01',
            })
        resolution = self.env['govoo.resolution'].with_company(company).create({
            'title': 'Standalone Shareholder Resolution',
            'resolution_type': 'ordinary',
        })
        resolution.action_open()
        return resolution

    def test_written_resolution_quorum_configured_rejects_too_few_votes(self):
        resolution = self._make_standalone_shareholder_resolution_with_holdings(0.5)
        # Only 1 of 4 eligible shareholders votes (25%) -- below 50%.
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'failed')

    def test_written_resolution_quorum_configured_passes_with_enough_votes(self):
        resolution = self._make_standalone_shareholder_resolution_with_holdings(0.5)
        # All 4 eligible shareholders vote (100%) -- clears 50% quorum.
        for partner in [self.partner_a, self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')

    def test_written_resolution_quorum_unset_preserves_always_met_behavior(self):
        resolution = self.env['govoo.resolution'].create({
            'title': 'Standalone Resolution No Quorum Config',
            'resolution_type': 'written',
        })
        resolution.action_open()
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')
