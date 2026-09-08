# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooEvaluationCampaign(models.Model):
    _name = 'govoo.evaluation.campaign'
    _description = 'Evaluation Campaign'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(
        string='Campaign Name',
        required=True,
        tracking=True,
    )
    committee_id = fields.Many2one(
        comodel_name='govoo.committee',
        string='Committee',
        tracking=True,
        ondelete='set null',
    )
    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string='Survey',
        required=True,
        tracking=True,
        ondelete='restrict',
        help='Standard Odoo survey used for this evaluation.',
    )
    evaluation_type = fields.Selection(
        selection=[
            ('board', 'Board Evaluation'),
            ('committee', 'Committee Evaluation'),
            ('peer', 'Peer Evaluation'),
            ('chair', 'Chair Evaluation'),
            ('self', 'Self Evaluation'),
        ],
        string='Evaluation Type',
        required=True,
        tracking=True,
    )
    participant_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Participants',
        tracking=True,
        help='Evaluators who will respond to the survey.',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    result_ids = fields.One2many(
        comodel_name='govoo.evaluation.result',
        inverse_name='campaign_id',
        string='Results',
    )
    response_count = fields.Integer(
        string='Responses',
        compute='_compute_response_count',
    )

    @api.depends('survey_id')
    def _compute_response_count(self):
        for rec in self:
            if rec.survey_id:
                rec.response_count = self.env['survey.user_input'].search_count([
                    ('survey_id', '=', rec.survey_id.id),
                    ('state', '=', 'done'),
                ])
            else:
                rec.response_count = 0

    @api.constrains('participant_ids', 'evaluation_type', 'committee_id')
    def _check_participants_are_committee_members(self):
        for rec in self:
            if rec.evaluation_type in ('board', 'committee', 'peer'):
                if not rec.committee_id:
                    raise ValidationError(
                        _('Committee is required for board, committee, '
                          'and peer evaluations.')
                    )
                if not rec.participant_ids:
                    raise ValidationError(
                        _('At least one participant is required for '
                          'board, committee, and peer evaluations.')
                    )
                member_partners = rec.committee_id.member_ids.mapped(
                    'partner_id',
                )
                invalid = rec.participant_ids - member_partners
                if invalid:
                    names = ', '.join(invalid.mapped('name'))
                    raise ValidationError(
                        _('Participants must be committee members. Invalid: %s') % names
                    )

    def action_open(self):
        """Transition draft -> open."""
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Only draft campaigns can be opened.'))
            if not rec.participant_ids:
                raise ValidationError(_('Cannot open campaign without participants.'))
            rec.state = 'open'
        return True

    def action_close(self):
        """Transition open -> closed and trigger aggregation."""
        for rec in self:
            if rec.state != 'open':
                raise ValidationError(_('Only open campaigns can be closed.'))
            rec.state = 'closed'
            rec._aggregate_results()
        return True

    def _aggregate_results(self):
        """Aggregate survey.user_input scores into govoo.evaluation.result.

        Called when campaign is closed. Creates or updates result records
        per survey page (dimension) with aggregate scores.
        """
        self.ensure_one()
        if not self.survey_id:
            return

        # Find all completed user inputs for this survey
        user_inputs = self.env['survey.user_input'].search([
            ('survey_id', '=', self.survey_id.id),
            ('state', '=', 'done'),
        ])

        if not user_inputs:
            return

        # Aggregate by question page (dimension)
        page_scores = {}
        page_counts = {}

        for user_input in user_inputs:
            for line in user_input.user_input_line_ids:
                page = line.question_id.page_id
                if not page:
                    continue
                page_id = page.id
                if page_id not in page_scores:
                    page_scores[page_id] = 0.0
                    page_counts[page_id] = 0
                if line.answer_score:
                    page_scores[page_id] += line.answer_score
                    page_counts[page_id] += 1

        # Create or update result records
        Result = self.env['govoo.evaluation.result']
        existing_results = Result.search([
            ('campaign_id', '=', self.id),
        ])
        existing_by_page = {
            r.dimension_id.id: r for r in existing_results
        }

        for page_id, total_score in page_scores.items():
            count = page_counts[page_id]
            avg_score = total_score / count if count else 0.0
            page = self.env['survey.question'].browse(page_id)

            if page_id in existing_by_page:
                existing_by_page[page_id].write({
                    'aggregate_score': avg_score,
                    'participant_count': count,
                })
            else:
                Result.create({
                    'campaign_id': self.id,
                    'dimension_id': page_id,
                    'aggregate_score': avg_score,
                    'participant_count': count,
                    'company_id': self.company_id.id,
                })

        # Remove results for pages that no longer have scores
        scored_pages = set(page_scores.keys())
        for page_id, result in existing_by_page.items():
            if page_id not in scored_pages:
                result.unlink()
