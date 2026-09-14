# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestGovooMinutesSignGate(GovooBoardTestBase):
    """BR-BOARD-008: e-signature legal-validity gate."""

    def _make_approved_minutes(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        return minutes

    def test_sign_blocked_without_confirmation_or_uploaded_document(self):
        """Default (unconfirmed) config: signing is blocked without a
        manually-uploaded signed document."""
        minutes = self._make_approved_minutes()
        with self.assertRaises(ValidationError):
            minutes.action_sign()

    def test_sign_allowed_via_manual_uploaded_document_fallback(self):
        """Unconfirmed config, but a signed document was uploaded first
        (the manual fallback path) -- signing proceeds."""
        minutes = self._make_approved_minutes()
        attachment = self.env['ir.attachment'].create({
            'name': 'signed.pdf',
            'datas': b'ZmFrZSBwZGY=',
        })
        minutes.signed_document_id = attachment
        minutes.action_sign()
        self.assertEqual(minutes.state, 'signed')

    def test_sign_allowed_when_legally_confirmed(self):
        """Config confirmed: signing proceeds without an uploaded document."""
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        minutes = self._make_approved_minutes()
        minutes.action_sign()
        self.assertEqual(minutes.state, 'signed')
