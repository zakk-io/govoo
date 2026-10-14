# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class TestBoardPackDistribution(GovooBoardTestBase):
    """Board Pack Distribution: real email (issue #203), sent in addition
    to (not instead of) the existing in-app portal notification."""

    def _compiled_pack(self):
        meeting = self._make_meeting()
        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        pack.action_compile()
        return pack

    def test_distribute_blocked_when_a_recipient_has_no_email(self):
        """The named pain point from the original request -- a missing
        email must block distribution with a clear error, not silently
        skip that recipient."""
        pack = self._compiled_pack()
        self.assertFalse(self.partner_a.email)
        with self.assertRaises(ValidationError):
            pack.action_distribute()

    def test_distribute_succeeds_and_sends_email_when_all_recipients_have_email(self):
        pack = self._compiled_pack()
        pack.distribution_ids.mapped('partner_id').write({'email': 'director@example.com'})
        mail_count_before = self.env['mail.mail'].search_count([])

        pack.action_distribute()

        self.assertEqual(pack.state, 'distributed')
        self.assertTrue(all(pack.distribution_ids.mapped('sent_date')))
        mail_count_after = self.env['mail.mail'].search_count([])
        self.assertGreater(
            mail_count_after, mail_count_before,
            'Distributing a pack should send a real email per recipient, '
            'in addition to the existing in-app notification.',
        )

    def test_distribute_still_posts_in_app_notification(self):
        """No regression: the existing portal chatter notification is
        still sent alongside the new email, not replaced by it."""
        pack = self._compiled_pack()
        pack.distribution_ids.mapped('partner_id').write({'email': 'director@example.com'})
        message_count_before = len(pack.message_ids)

        pack.action_distribute()

        self.assertGreater(len(pack.message_ids), message_count_before)

    def test_distribute_is_idempotent_for_already_sent_recipients(self):
        """A recipient with sent_date already set is not re-emailed on a
        second call -- matches the existing 'if not dist.sent_date' guard."""
        pack = self._compiled_pack()
        pack.distribution_ids.mapped('partner_id').write({'email': 'director@example.com'})
        pack.action_distribute()
        first_sent_dates = {d.id: d.sent_date for d in pack.distribution_ids}

        # Re-running distribute (e.g. state manually reset to compiled)
        # must not change already-sent recipients' sent_date.
        pack.state = 'compiled'
        pack.action_distribute()
        for dist in pack.distribution_ids:
            self.assertEqual(dist.sent_date, first_sent_dates[dist.id])

    def test_distribute_requires_compiled_state(self):
        meeting = self._make_meeting()
        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        with self.assertRaises(ValidationError):
            pack.action_distribute()

    # -- Issue #271 item 6: minimum board-pack distribution lead time ----

    def test_lead_time_unset_preserves_default_behavior(self):
        """Unset (default): a pack can be distributed at any time relative
        to the meeting date -- the original behavior."""
        pack = self._compiled_pack()
        pack.meeting_id.date = fields.Datetime.now() - timedelta(days=1)
        pack.distribution_ids.mapped('partner_id').write({'email': 'director@example.com'})
        pack.action_distribute()
        self.assertEqual(pack.state, 'distributed')

    def test_lead_time_blocks_distribution_too_close_to_meeting(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.board_pack_min_lead_days', '5',
        )
        pack = self._compiled_pack()
        pack.meeting_id.date = fields.Datetime.now() + timedelta(days=2)
        pack.distribution_ids.mapped('partner_id').write({'email': 'director@example.com'})
        with self.assertRaises(ValidationError):
            pack.action_distribute()

    def test_lead_time_allows_distribution_far_enough_out(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.board_pack_min_lead_days', '5',
        )
        pack = self._compiled_pack()
        pack.meeting_id.date = fields.Datetime.now() + timedelta(days=10)
        pack.distribution_ids.mapped('partner_id').write({'email': 'director@example.com'})
        pack.action_distribute()
        self.assertEqual(pack.state, 'distributed')
