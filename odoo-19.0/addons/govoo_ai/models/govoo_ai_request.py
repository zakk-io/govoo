# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Issue #214 found that the source addendum's §2.2 feature table is missing
# rows for AI-F02, AI-F03 and AI-F06 -- no description exists anywhere in
# this repository for what they cover. They are deliberately left out of
# this selection rather than guessed at; add them here only once
# docs/ai_services_layer_clagov_ai.md is corrected with real content.
AI_FEATURE_SELECTION = [
    ('ai_f01', 'AI-F01: Minute Drafting'),
    ('ai_f04', 'AI-F04: Board-Pack Summarization'),
    ('ai_f05', 'AI-F05: Agenda Drafting'),
    ('ai_f07', 'AI-F07: Data Extraction'),
    ('ai_f08', 'AI-F08: Semantic Search (RAG)'),
    ('ai_f09', 'AI-F09: Governance Q&A'),
    ('ai_f10', 'AI-F10: Regulatory Horizon-Scanning'),
    ('ai_f11', 'AI-F11: Deadline Risk Scoring'),
    ('ai_f12', 'AI-F12: Narrative Drafting'),
    ('ai_f13', 'AI-F13: Anomaly Detection'),
    ('ai_f14', 'AI-F14: Evaluation Analysis'),
    ('ai_f15', 'AI-F15: Director Knowledge Assistant'),
    ('ai_f16', 'AI-F16: Assisted Translation'),
]


class GovooAiRequest(models.Model):
    _name = 'govoo.ai.request'
    _description = 'AI Request Log'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    feature = fields.Selection(
        selection=AI_FEATURE_SELECTION,
        string='Feature',
        required=True,
        tracking=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Invoked By',
        required=True,
        default=lambda self: self.env.user,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    model_name = fields.Char(
        string='Model Used',
        help='Provider + model version actually used for this call, '
             'e.g. "openai:gpt-4o" -- filled in once the call completes.',
    )
    input_ref = fields.Char(
        string='Input Reference',
        help='Source record(s) this request was generated from, '
             'e.g. "govoo.meeting,42".',
    )
    input_summary = fields.Text(
        string='Input Summary (Redacted)',
        help='AI-N06: a redacted summary of what was sent to the model -- '
             'never the raw, unredacted prompt. Redaction must happen in '
             'the calling feature cluster before this field is written; '
             'this layer does not inspect or scrub the text itself.',
    )
    output_ref = fields.Reference(
        selection=[('govoo.ai.suggestion', 'AI Suggestion')],
        string='Output',
        help='The suggestion this request produced. Limited to '
             'govoo.ai.suggestion for now -- every AI output goes through '
             'the human-review queue, never a direct write elsewhere.',
    )
    token_usage = fields.Integer(
        string='Token Usage',
        default=0,
        help='Filled in once the call completes; used for '
             'govoo.ai.config.monthly_token_cap enforcement.',
    )
    status = fields.Selection(
        selection=[
            ('queued', 'Queued'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='queued',
        required=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Gate every request on the company's AI config (AI-N07): no
        request is queued unless AI is explicitly enabled for that company,
        and only up to its configured monthly_token_cap. This is the
        commercial cost-control mechanism as much as it is a guardrail --
        govoo_ai is a metered paid add-on (see docs/ai_services_layer_
        clagov_ai.md §1)."""
        Config = self.env['govoo.ai.config'].sudo()
        for vals in vals_list:
            company_id = vals.get('company_id') or self.env.company.id
            config = Config.search([('company_id', '=', company_id)], limit=1)
            if not config or not config.active:
                raise ValidationError(_(
                    'AI features are not enabled for this company. '
                    'An AI Administrator must activate govoo.ai.config first.'
                ))
            feature = vals.get('feature')
            if feature and not config.is_feature_enabled(feature):
                raise ValidationError(_(
                    'The "%s" AI feature is not enabled for this company.'
                ) % dict(AI_FEATURE_SELECTION).get(feature, feature))
            month_start = fields.Datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0,
            )
            used = sum(self.sudo().search([
                ('company_id', '=', company_id),
                ('create_date', '>=', month_start),
            ]).mapped('token_usage'))
            if used >= config.monthly_token_cap:
                raise ValidationError(_(
                    'This company has reached its monthly AI token cap '
                    '(%s). Contact your AI Administrator to raise it.'
                ) % config.monthly_token_cap)
        return super().create(vals_list)

    @api.model
    def _cron_process_queued(self):
        """Extension point for consumer feature clusters (issue #214's
        AI-F* children): this layer only defines the queue/status contract
        (AI-N07 -- no feature cluster blocks its request thread on a live
        model call). No AI-F feature has been implemented yet (see #214),
        so there is nothing to dispatch to; a queued request is left
        queued rather than silently marked done/failed. Once a consumer
        cluster registers real dispatch logic, this method's body is where
        it hooks in -- not a per-feature cron of its own.
        """
        queued = self.search([('status', '=', 'queued')])
        if queued:
            _logger.info(
                '%s govoo.ai.request record(s) queued with no registered '
                'dispatch handler yet (no AI-F feature cluster is '
                'implemented). Left queued.', len(queued),
            )
