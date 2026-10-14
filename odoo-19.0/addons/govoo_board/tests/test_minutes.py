# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

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
        """Without an active govoo_rw retention rule, retention_until
        defaults to 10 years. Guards against govoo_rw actually being
        installed (as it is in this shared dev database, with its own
        seeded 'minutes' rule) by deactivating any such rule first --
        govoo_board's own suite is written to run with govoo_rw absent,
        so this reproduces that condition regardless of the DB it runs
        against."""
        if 'govoo.rw.retention' in self.env:
            self.env['govoo.rw.retention'].search([
                ('retention_category', '=', 'minutes'),
                ('company_id', '=', self.company.id),
            ]).write({'active': False})
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
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

        # BR-BOARD-008: signing is blocked unless e-signature legal validity
        # is confirmed (or a signed document is manually uploaded) -- not
        # this test's concern (Enterprise/Community feature-flagging),
        # so confirm it to isolate that path.
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        minutes.action_submit_for_approval()
        minutes.action_approve()
        minutes.action_sign()

        self.assertEqual(minutes.state, 'signed')


@tagged('post_install', '-at_install', 'govoo_board')
class TestGovooMinutesActorTracking(GovooBoardTestBase):
    """Issue #271 item 1: audit-trail fields + self-approval guard."""

    def _make_minutes_held(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        return self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })

    def test_actor_fields_set_on_each_transition(self):
        minutes = self._make_minutes_held()
        minutes.action_submit_for_approval()
        self.assertEqual(minutes.submitted_by_id, self.env.user)
        minutes.action_approve()
        self.assertEqual(minutes.approved_by_id, self.env.user)
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        minutes.action_sign()
        self.assertEqual(minutes.signed_by_id, self.env.user)

    def test_self_approval_allowed_by_default(self):
        """Unset config: the same user who submitted may still approve --
        the original behavior."""
        minutes = self._make_minutes_held()
        minutes.action_submit_for_approval()
        minutes.action_approve()
        self.assertEqual(minutes.state, 'approved')

    def test_self_approval_blocked_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.minutes_require_different_approver', 'True',
        )
        minutes = self._make_minutes_held()
        minutes.action_submit_for_approval()
        with self.assertRaises(ValidationError):
            minutes.action_approve()

    def test_different_approver_allowed_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.minutes_require_different_approver', 'True',
        )
        minutes = self._make_minutes_held()
        minutes.action_submit_for_approval()
        other_secretary = new_test_user(
            self.env, login='test_other_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        minutes.with_user(other_secretary).action_approve()
        self.assertEqual(minutes.state, 'approved')
        self.assertEqual(minutes.approved_by_id, other_secretary)

    def test_submitting_for_approval_notifies_secretaries(self):
        """Issue #271 follow-up: previously nobody was told minutes needed
        approval. assertGreater (not an exact count) since
        get_governance_secretary_partners() is not company-scoped and may
        also notify real secretaries already seeded in the shared dev DB."""
        message_count_before = self.env['mail.message'].search_count([])
        mail_count_before = self.env['mail.mail'].search_count([])

        minutes = self._make_minutes_held()
        minutes.action_submit_for_approval()

        self.assertGreater(self.env['mail.message'].search_count([]), message_count_before)
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_submitter_excluded_from_their_own_notification_when_require_different_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.minutes_require_different_approver', 'True',
        )
        secretary = new_test_user(
            self.env, login='test_notify_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        minutes = self._make_minutes_held().with_user(secretary)
        minutes.action_submit_for_approval()

        notified_partners = minutes.message_ids.mapped('partner_ids')
        self.assertNotIn(secretary.partner_id, notified_partners)


@tagged('post_install', '-at_install', 'govoo_board')
class TestGovooMinutesContentLock(GovooBoardTestBase):
    """Issue #271 item 5: approved/signed minutes content is immutable."""

    def _make_approved_minutes(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Original content.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        return minutes

    def test_body_editable_before_approval(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Draft content.</p>',
        })
        minutes.body = '<p>Revised draft.</p>'
        self.assertIn('Revised draft', minutes.body)

    def test_body_locked_after_approval(self):
        minutes = self._make_approved_minutes()
        with self.assertRaises(ValidationError):
            minutes.body = '<p>Tampered content.</p>'

    def test_attendance_locked_after_approval(self):
        minutes = self._make_approved_minutes()
        with self.assertRaises(ValidationError):
            minutes.attendance_ids = [(6, 0, [self.partner_a.id])]

    def test_apologies_locked_after_approval(self):
        minutes = self._make_approved_minutes()
        with self.assertRaises(ValidationError):
            minutes.apologies_ids = [(6, 0, [self.partner_a.id])]

    def test_signed_document_still_writable_after_approval(self):
        """The manual-upload-fallback path sets this field while still
        'approved', before action_sign() -- must not be swept into the
        content lock."""
        minutes = self._make_approved_minutes()
        attachment = self.env['ir.attachment'].create({
            'name': 'signed.pdf',
            'datas': b'ZmFrZSBwZGY=',
        })
        minutes.signed_document_id = attachment
        self.assertEqual(minutes.signed_document_id, attachment)
