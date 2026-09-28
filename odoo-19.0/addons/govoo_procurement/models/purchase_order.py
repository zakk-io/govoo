# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    govoo_tender_id = fields.Many2one(
        comodel_name='govoo.tender',
        string='Tender',
        ondelete='set null',
        tracking=True,
        help='Links this vendor bid (a normal RFQ/purchase order) to the '
             "governance-tracked tender case file it's part of.",
    )
    govoo_technical_score = fields.Float(
        string='Technical Score',
        tracking=True,
        help='[CONFIRM] The scoring scale and technical-vs-financial '
             'weighting for tender evaluation are not specified (issue '
             '#205 sub-task). Recorded here as a plain 0-100 score per '
             'the committee\'s own methodology; no combined/weighted '
             'score is computed until that weighting is confirmed.',
    )
    govoo_financial_score = fields.Float(
        string='Financial Score',
        tracking=True,
        help='[CONFIRM] See govoo_technical_score -- weighting not yet confirmed.',
    )

    @api.constrains('govoo_technical_score', 'govoo_financial_score')
    def _check_govoo_scores_range(self):
        for rec in self:
            for field_name in ('govoo_technical_score', 'govoo_financial_score'):
                value = rec[field_name]
                if value and not (0 <= value <= 100):
                    raise ValidationError(_(
                        '%s must be between 0 and 100.'
                    ) % rec._fields[field_name].string)
