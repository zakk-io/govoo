# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestGovooMinutesDelete(GovooBoardTestBase):
    """access-control.md: Secretary D restricted post-approval (draft/
    for_approval deletable, approved/signed blocked)."""

    def test_delete_allowed_in_draft(self):
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.unlink()
        self.assertFalse(minutes.exists())

    def test_delete_allowed_in_for_approval(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        self.assertEqual(minutes.state, 'for_approval')
        minutes.unlink()
        self.assertFalse(minutes.exists())

    def test_delete_blocked_once_approved(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        self.assertEqual(minutes.state, 'approved')
        with self.assertRaises(ValidationError):
            minutes.unlink()


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


@tagged('post_install', '-at_install')
class TestGovooMinutesRetention(GovooBoardTestBase):
    """govoo_board does not depend on govoo_rw; this suite only exercises
    the fallback path (BR-BOARD-004). The real govoo.rw.retention lookup
    is covered in govoo_rw's own tests, which do depend on govoo_board."""

    def test_retention_until_falls_back_to_ten_years_without_govoo_rw(self):
        """Without govoo_rw installed, retention_until defaults to 10 years."""
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        self.assertTrue('govoo.rw.retention' not in self.env)
        expected = minutes.create_date.date().replace(
            year=minutes.create_date.year + 10,
        )
        self.assertEqual(minutes.retention_until, expected)


@tagged('post_install', '-at_install')
class TestMinutesWorkflow(GovooBoardTestBase):
    """TC-WF-BOARD-003: draft -> for_approval -> approved, retention_until
    computed. govoo_board's own suite has no govoo_rw installed, so this
    exercises the documented fallback default (10 years); the real
    govoo_rw-config path is covered in govoo_rw's own test suite (#32)."""

    def test_minutes_lifecycle_and_retention(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        self.assertEqual(minutes.state, 'draft')

        minutes.action_submit_for_approval()
        self.assertEqual(minutes.state, 'for_approval')

        minutes.action_approve()
        self.assertEqual(minutes.state, 'approved')

        expected_retention = minutes.create_date.date().replace(
            year=minutes.create_date.year + 10,
        )
        self.assertEqual(minutes.retention_until, expected_retention)
