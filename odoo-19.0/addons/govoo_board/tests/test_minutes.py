# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooMinutesAcceptanceTC(GovooBoardTestBase):
    """TC-ACC-009: Enterprise feature graceful degradation."""

    def test_sign_completes_without_sign_app_or_signed_document(self):
        """TC-ACC-009: minutes reach 'signed' on Community, with no Sign
        app and no signed_document_id attached, without an unhandled
        error. Signing is feature-flagged (ir.attachment on Community vs
        documents.document on Enterprise) and must not hard-depend on
        either being present."""
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()

        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        self.assertFalse(minutes.signed_document_id)

        minutes.action_submit_for_approval()
        minutes.action_approve()
        minutes.action_sign()

        self.assertEqual(minutes.state, 'signed')
