# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    @api.depends('create_date')
    def _compute_retention_until(self):
        """10 years retention from create_date via govoo_rw config.

        [CONFIRM] The literal source is govoo_rw retention config;
        if not yet available, defaults to 10 years.
        """
        for rec in self:
            if rec.create_date:
                rec.retention_until = rec.create_date.replace(
                    year=rec.create_date.year + 10,
                )
            else:
                rec.retention_until = False

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
                        'E-signature is not yet confirmed as legally valid '
                        'under Rwandan law (BR-BOARD-008). Upload the signed '
                        'copy to "Signed Document" first, then sign.'
                    ))
        self._validate_state_transition('signed')
        self.write({'state': 'signed'})
