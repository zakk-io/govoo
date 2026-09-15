# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GovooEvaluationResult(models.Model):
    """Aggregate evaluation results, derived from survey.user_input.

    aggregate_score/participant_count are intentionally plain fields,
    not compute=/@api.depends: they're a point-in-time snapshot taken
    when the campaign closes (govoo_evaluation_campaign._aggregate_results),
    not a live-recomputing value -- a real compute would recalculate
    whenever a dependency changes, but this value must stay frozen at
    close time even if survey responses change afterward. There's also
    no direct stored relation from this model to survey.user_input for
    @api.depends to track (the join is via campaign_id.survey_id
    matching survey_id). Protected instead via readonly=True plus a
    write-guard restricted to the aggregation code path.
    """
    _name = 'govoo.evaluation.result'
    _description = 'Evaluation Result (Aggregate)'
    _order = 'campaign_id, dimension_id'

    campaign_id = fields.Many2one(
        comodel_name='govoo.evaluation.campaign',
        string='Campaign',
        required=True,
        ondelete='cascade',
    )
    dimension_id = fields.Many2one(
        comodel_name='survey.question',
        string='Dimension',
        help='Survey page used as evaluation dimension.',
        domain=[('is_page', '=', True)],
    )
    dimension_name = fields.Char(
        string='Dimension Name',
        related='dimension_id.title',
        store=True,
    )
    aggregate_score = fields.Float(
        string='Aggregate Score',
        digits=(10, 2),
        readonly=True,
        help='Average score across all respondents for this dimension. '
             'Derived data, set only when the campaign is closed -- never '
             'edit directly; correct the underlying survey responses instead.',
    )
    participant_count = fields.Integer(
        string='Participants',
        readonly=True,
        help='Number of respondents contributing to this aggregate. '
             'Derived data, set only when the campaign is closed -- never '
             'edit directly; correct the underlying survey responses instead.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )

    @api.depends('campaign_id')
    def _compute_company(self):
        for rec in self:
            if rec.campaign_id:
                rec.company_id = rec.campaign_id.company_id

    _GUARDED_FIELDS = ('aggregate_score', 'participant_count')

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('govoo_aggregation'):
            for vals in vals_list:
                if any(f in vals for f in self._GUARDED_FIELDS):
                    raise UserError(
                        _('aggregate_score/participant_count are derived data, set only '
                          'when the campaign is closed. Correct the underlying survey '
                          'responses instead of editing the aggregate directly.')
                    )
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get('govoo_aggregation'):
            if any(f in vals for f in self._GUARDED_FIELDS):
                raise UserError(
                    _('aggregate_score/participant_count are derived data, set only '
                      'when the campaign is closed. Correct the underlying survey '
                      'responses instead of editing the aggregate directly.')
                )
        return super().write(vals)
