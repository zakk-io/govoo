# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooAiSuggestion(models.Model):
    _name = 'govoo.ai.suggestion'
    _description = 'AI Suggestion'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    request_id = fields.Many2one(
        comodel_name='govoo.ai.request',
        string='Request',
        required=True,
        ondelete='cascade',
    )
    target_model = fields.Char(
        string='Target Model',
        required=True,
        help='Technical model name this suggestion applies to, '
             'e.g. "govoo.minutes". This layer never writes to it directly '
             '-- applying an accepted suggestion is each consumer feature '
             "cluster's own responsibility, using whatever logic is "
             'correct for that model.',
    )
    target_res_id = fields.Integer(
        string='Target Record ID',
        help='Empty when the suggestion is for a new record not yet created.',
    )
    content = fields.Html(
        string='Suggested Content',
    )
    confidence = fields.Float(
        string='Confidence',
        help='0.0-1.0 indicator.',
    )
    citations = fields.Text(
        string='Citations',
        help='AI-N04: grounding sources for this suggestion. A citation-'
             'producing feature (e.g. AI-F08/AI-F09) should never leave '
             'this empty for a grounded answer.',
    )
    extracted_values = fields.Text(
        string='Extracted Values',
        help='AI-F07 only: a JSON-serialized {field_name: value} dict '
             'proposed for target_model, for review before any real '
             'record is created from it. Relation fields carry the '
             'extracted text (e.g. a name), never a guessed id -- '
             'resolving that to a real record is the reviewing human\'s '
             'own confirmation, not something trusted from the model\'s '
             'own output (AI-N02/AI-N04).',
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('edited', 'Edited'),
        ],
        string='Status',
        default='pending',
        required=True,
        tracking=True,
    )
    reviewed_by = fields.Many2one(
        comodel_name='res.users',
        string='Reviewed By',
        readonly=True,
        copy=False,
    )
    reviewed_date = fields.Datetime(
        string='Reviewed On',
        readonly=True,
        copy=False,
    )

    @api.constrains('confidence')
    def _check_confidence_range(self):
        for rec in self:
            if rec.confidence and not (0 <= rec.confidence <= 1):
                raise ValidationError(_('Confidence must be between 0 and 1.'))

    def write(self, vals):
        """AI-N03 (human-in-the-loop): state may only change via
        action_accept()/action_reject()/action_mark_edited() below, never
        by a direct write -- this is the ORM-level enforcement the
        guardrail needs, not just a hidden UI button."""
        if 'state' in vals and not self.env.context.get('govoo_ai_suggestion_internal'):
            raise ValidationError(_(
                'A suggestion\'s status can only change via Accept/Reject, '
                'never by editing the field directly.'
            ))
        return super().write(vals)

    def _mark_reviewed(self, state):
        for rec in self:
            if rec.state != 'pending':
                raise ValidationError(_(
                    'Only a pending suggestion can be reviewed (current status: %s).'
                ) % dict(rec._fields['state'].selection).get(rec.state))
        self.with_context(govoo_ai_suggestion_internal=True).write({
            'state': state,
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_accept(self):
        """Marks this suggestion accepted. Does NOT write target_model/
        target_res_id itself -- the calling feature cluster applies the
        content to the real record as part of its own accept flow, then
        calls this to close out the review queue entry. Keeping the two
        steps separate is deliberate: this layer cannot safely know how to
        apply an arbitrary suggestion to an arbitrary target model."""
        self._mark_reviewed('accepted')

    def action_reject(self):
        self._mark_reviewed('rejected')

    def action_open_target(self):
        """Open the suggestion's target record in a form view.

        Used by search-style features (e.g. AI-F08) where the suggestion
        itself is the result, not a draft to accept into a record. Relies
        on the model's own access control -- opening a record the user
        cannot read fails exactly as it would from any other Odoo link.

        :raise ValidationError: if target_model/target_res_id name no
            record (empty, unknown model, or already deleted).
        """
        self.ensure_one()
        if not self.target_model or not self.target_res_id:
            raise ValidationError(_('This suggestion has no target record to open.'))
        if self.target_model not in self.env:
            raise ValidationError(_('Unknown model: %s') % self.target_model)
        record = self.env[self.target_model].browse(self.target_res_id)
        if not record.exists():
            raise ValidationError(_(
                '%(model)s(%(id)s) no longer exists.'
            ) % {'model': self.target_model, 'id': self.target_res_id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.target_model,
            'res_id': self.target_res_id,
            'views': [(False, 'form')],
            'target': 'current',
        }
