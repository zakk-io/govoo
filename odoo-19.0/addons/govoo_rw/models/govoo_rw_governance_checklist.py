# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooRwGovernanceChecklistItem(models.Model):
    """CMA Corporate Governance Code self-assessment checklist item
    (FR-RW-004): an "apply-and-explain" checklist, linked to the
    compliance instance generated from the CMA governance-code
    obligation, reusing the govoo_compliance pattern rather than a
    bespoke model.

    [CONFIRM] No provision content is seeded here -- the actual CMA
    Corporate Governance Code 2024 provisions/numbering require legal
    advisor confirmation before being entered (see
    docs/spec/decisions/open-decisions.md), consistent with this
    module's own rule against shipping hard-coded legal values.
    """
    _name = 'govoo.rw.governance.checklist.item'
    _description = 'CMA Governance Code Checklist Item'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    instance_id = fields.Many2one(
        comodel_name='govoo.compliance.instance',
        string='Compliance Instance',
        required=True,
        ondelete='cascade',
        help='The CMA governance self-assessment compliance instance this item belongs to.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='instance_id.company_id',
        store=True,
        readonly=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    provision_ref = fields.Char(
        string='Provision Reference',
        required=True,
        tracking=True,
        help='Reference to the specific CMA Corporate Governance Code provision/principle.',
    )
    description = fields.Text(
        string='Provision Description',
    )
    status = fields.Selection(
        selection=[
            ('comply', 'Comply'),
            ('explain', 'Explain'),
            ('not_applicable', 'Not Applicable'),
        ],
        string='Status',
        tracking=True,
    )
    explanation = fields.Text(
        string='Explanation',
        help='Required narrative when status is "Explain", per the apply-and-explain methodology.',
    )

    @api.constrains('status', 'explanation')
    def _check_explanation_required_when_explain(self):
        for rec in self:
            if rec.status == 'explain' and not rec.explanation:
                raise ValidationError(
                    _('An explanation is required when status is "Explain" '
                      '(apply-and-explain methodology).')
                )
