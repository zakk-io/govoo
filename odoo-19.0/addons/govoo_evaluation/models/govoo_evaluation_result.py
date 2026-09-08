# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class GovooEvaluationResult(models.Model):
    _name = 'govoo.evaluation.result'
    _description = 'Evaluation Result (Aggregate)'
    _inherit = ['mail.thread']
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
        help='Average score across all respondents for this dimension.',
    )
    participant_count = fields.Integer(
        string='Participants',
        help='Number of respondents contributing to this aggregate.',
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
