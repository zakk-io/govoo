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
    # Feature-flagged: ir.attachment (Community) / documents.document (Enterprise)
    signed_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Signed Document',
    )
    retention_until = fields.Date(
        string='Retention Until',
        compute='_compute_retention_until',
        store=True,
    )

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
                    rec.company_id.id, _DEFAULT_RETENTION_YEARS, rec.id or 'new',
                )
                rec.retention_until = rec.create_date.replace(
                    year=rec.create_date.year + _DEFAULT_RETENTION_YEARS,
                )

    @api.constrains('state')
    def _check_state_no_delete_after_draft(self):
        """No delete once state != draft."""
        # Enforced via unlink override

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Cannot delete minutes once they leave draft status.'))
        return super().unlink()

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
        self.write({'state': 'for_approval'})

    def action_approve(self):
        self._validate_state_transition('approved')
        self.write({'state': 'approved'})

    def action_sign(self):
        """Gated on [CONFIRM] legal validity of e-signature (BR-BOARD-008).

        Feature-flagged: sign_request_id usage depends on sign module availability.
        """
        self._validate_state_transition('signed')
        self.write({'state': 'signed'})
