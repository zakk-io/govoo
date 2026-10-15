# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Fallback only -- used when govoo_rw isn't installed or has no active
# 'minutes' retention rule for the company. Never the primary source
# (BR-BOARD-004): govoo_rw's govoo.rw.retention config is authoritative
# when available.
_DEFAULT_RETENTION_YEARS = 10


class GovooMinutes(models.Model):
    _name = 'govoo.minutes'
    _description = 'Meeting Minutes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    meeting_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Meeting',
        required=True,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='meeting_id.company_id',
        store=True,
        readonly=True,
    )
    body = fields.Html(
        string='Minutes Content',
    )
    attendance_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='govoo_minutes_attendance_rel',
        column1='minutes_id',
        column2='partner_id',
        string='Attendance',
    )
    apologies_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='govoo_minutes_apologies_rel',
        column1='minutes_id',
        column2='partner_id',
        string='Apologies',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('for_approval', 'For Approval'),
            ('approved', 'Approved'),
            ('signed', 'Signed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
    signed_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Signed Document',
    )
    retention_until = fields.Date(
        string='Retention Until',
        compute='_compute_retention_until',
        store=True,
    )
    submitted_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
    )
    approved_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
        readonly=True,
        copy=False,
    )
    signed_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Signed By',
        readonly=True,
        copy=False,
    )

    _LOCKED_FIELDS_AFTER_APPROVAL = ('body', 'attendance_ids', 'apologies_ids')

    @api.depends('meeting_id.name')
    def _compute_display_name(self):
        # No plain-text field on this model, so display_name would
        # otherwise fall back to the raw "govoo.minutes,<id>" string.
        for rec in self:
            rec.display_name = _('Minutes - %s') % rec.meeting_id.name \
                if rec.meeting_id else _('Minutes')

    @api.model_create_multi
    def create(self, vals_list):
        """Link the meeting back to these minutes on creation, mirroring
        govoo.board.pack.create()'s own meeting.pack_id link-back. Without
        this, meeting.minutes_id (a plain, non-computed field with no
        editable widget anywhere in the UI) stays permanently unset for
        every minutes record created via the normal "Draft Minutes"
        button -- action_minute()'s own 'Minutes must be created before
        marking meeting as minuted' check would then always fail, even
        once the minutes are genuinely drafted and approved, with no way
        to fix it from the UI at all."""
        records = super().create(vals_list)
        for rec in records:
            if rec.meeting_id and not rec.meeting_id.minutes_id:
                rec.meeting_id.minutes_id = rec.id
        return records

    @api.depends('create_date', 'company_id')
    def _compute_retention_until(self):
        """Retention from create_date, sourced from govoo_rw config (BR-BOARD-004).

        govoo_board does not depend on govoo_rw (govoo_rw already depends
        on govoo_board -- a real dependency would be circular), so the
        govoo.rw.retention model is looked up via a guarded ORM access
        instead of a manifest dependency. Falls back to a 10-year default,
        logged, only when govoo_rw isn't installed or has no active
        'minutes' rule for the company.
        """
        has_govoo_rw = 'govoo.rw.retention' in self.env
        # [CONFIRM] open-decisions.md item 13 (10-year statutory retention vs.
        # data-subject erasure rights). Admin-editable via Configuration >
        # Governance Settings (issue #238); _DEFAULT_RETENTION_YEARS remains
        # the hardcoded default-of-defaults for a brand-new install.
        fallback_years = int(self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.minutes_retention_default_years', _DEFAULT_RETENTION_YEARS,
        ))
        for rec in self:
            if not rec.create_date:
                rec.retention_until = False
                continue

            rule = None
            if has_govoo_rw:
                rule = self.env['govoo.rw.retention'].search([
                    ('retention_category', '=', 'minutes'),
                    ('active', '=', True),
                    ('company_id', '=', rec.company_id.id),
                ], limit=1)

            if rule:
                rec.retention_until = rule.get_retention_date(rec.create_date)
            else:
                _logger.warning(
                    'No active govoo.rw.retention rule found for category '
                    '"minutes" in company %s; falling back to the %s-year '
                    'default for minutes id %s.',
                    rec.company_id.id, fallback_years, rec.id or 'new',
                )
                rec.retention_until = rec.create_date.replace(
                    year=rec.create_date.year + fallback_years,
                )

    @api.constrains('state')
    def _check_state_no_delete_after_draft(self):
        """No delete once state != draft."""
        # Enforced via unlink override

    def unlink(self):
        for rec in self:
            if rec.state in ('approved', 'signed'):
                raise ValidationError(_('Cannot delete minutes once approved.'))
        return super().unlink()

    def write(self, vals):
        """Issue #271 item 5: lock substantive content once approved --
        only unlink() was previously guarded, so the body/attendance could
        still be silently changed after "Approval" in effect meant
        nothing. signed_document_id is deliberately NOT locked (the
        manual-upload-fallback path sets it while still 'approved', before
        action_sign())."""
        if any(f in vals for f in self._LOCKED_FIELDS_AFTER_APPROVAL):
            for rec in self:
                if rec.state in ('approved', 'signed'):
                    raise ValidationError(_(
                        'Minutes content cannot be edited once approved.'
                    ))
        return super().write(vals)

    def _validate_state_transition(self, target_state):
        """Enforce strictly forward state transitions."""
        allowed = {
            'draft': ['for_approval'],
            'for_approval': ['approved'],
            'approved': ['signed'],
        }
        for rec in self:
            if target_state not in allowed.get(rec.state, []):
                raise ValidationError(
                    _('Cannot transition from "%s" to "%s". '
                      'Minutes state must advance strictly forward.')
                    % (rec.state, target_state),
                )

    def action_submit_for_approval(self):
        self._validate_state_transition('for_approval')
        for rec in self:
            if rec.meeting_id.state not in ('held', 'minuted', 'closed'):
                raise ValidationError(
                    _('Meeting must be at least "Held" before submitting minutes for approval.')
                )
        self.write({'state': 'for_approval', 'submitted_by_id': self.env.uid})
        self._notify_approvers()

    def _notify_approvers(self):
        """Issue #271 follow-up: nobody was told minutes needed their
        approval -- they'd only find out by opening the Minutes list
        manually. Notifies every Company Secretary (the only group with
        write access to govoo.minutes, confirmed via ir.model.access.csv
        -- Admin is read-only here), reusing the same
        get_governance_secretary_partners() helper and per-recipient
        send_mail(email_values=...) loop govoo_secretarial_cron.py's
        _notify_secretaries() already established. Excludes the submitter
        when minutes_require_different_approver is on, since they're
        blocked from approving their own submission anyway -- notifying
        them to do something they can't would be misleading."""
        require_different = self._minutes_require_different_approver()
        template = self.env.ref(
            'govoo_board.mail_template_minutes_approval_requested', raise_if_not_found=False,
        )
        for rec in self:
            secretaries = self.env['res.users'].get_governance_secretary_partners()
            if require_different and rec.submitted_by_id:
                secretaries = secretaries - rec.submitted_by_id.partner_id
            for partner in secretaries:
                rec.message_post(
                    body=_('Minutes for %s are awaiting your approval.') % rec.meeting_id.name,
                    partner_ids=partner.ids,
                    subtype_xmlid='mail.mt_comment',
                )
                if template:
                    template.send_mail(
                        rec.id,
                        email_values={
                            'email_to': partner.email,
                            'recipient_ids': [(6, 0, partner.ids)],
                        },
                        force_send=True,
                    )

    def _minutes_require_different_approver(self):
        """Issue #271 item 1: unset/False preserves the original behavior
        (the same Secretary who drafted and submitted may also approve).
        Does not implement a full "Directors approve" workflow -- no
        non-portal Director/Chair role exists in this codebase to grant
        write access to govoo.minutes to (see issue #271's scope note);
        this only prevents the narrowest form of self-approval."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.minutes_require_different_approver', 'False',
        ) in ('True', '1')

    def action_approve(self):
        self._validate_state_transition('approved')
        require_different = self._minutes_require_different_approver()
        for rec in self:
            if (
                require_different
                and rec.submitted_by_id
                and rec.submitted_by_id.id == self.env.uid
            ):
                raise ValidationError(_(
                    'Cannot approve: these minutes must be approved by '
                    'someone other than whoever submitted them.'
                ))
        self.write({'state': 'approved', 'approved_by_id': self.env.uid})

    @api.model
    def _esignature_legally_confirmed(self):
        """BR-BOARD-008: legal validity of e-signature under Rwandan law is
        still an open decision (docs/spec/decisions/open-decisions.md #3) --
        defaults to unconfirmed.
        """
        confirmed = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.e_signature_legally_confirmed', 'False',
        )
        return confirmed in ('True', '1')

    def action_sign(self):
        """Gated on [CONFIRM] legal validity of e-signature (BR-BOARD-008).

        While unconfirmed, the e-sign integration path is closed and
        'signed' is only reachable via the manual "signed copy uploaded"
        fallback -- forced here by requiring signed_document_id to already
        be set. Not a runtime error to work around by retrying; a
        build-time/config gate (docs/spec/workflows/minutes.md).
        """
        if not self._esignature_legally_confirmed():
            for rec in self:
                if not rec.signed_document_id:
                    raise ValidationError(_(
                        'E-signature has not yet been confirmed as legally '
                        'valid. Upload the signed copy to "Signed Document" '
                        'first, then sign.'
                    ))
        self._validate_state_transition('signed')
        self.write({'state': 'signed', 'signed_by_id': self.env.uid})
