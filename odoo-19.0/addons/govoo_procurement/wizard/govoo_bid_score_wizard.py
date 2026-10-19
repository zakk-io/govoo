# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class GovooBidScoreWizard(models.TransientModel):
    _name = 'govoo.bid.score.wizard'
    _description = 'Submit Technical/Financial Score for a Vendor Bid'

    bid_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Vendor Bid',
        required=True,
        readonly=True,
    )
    govoo_technical_score = fields.Float(string='Technical Score')
    govoo_financial_score = fields.Float(string='Financial Score')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get('bid_id'):
            bid = self.env['purchase.order'].browse(res['bid_id'])
            res.setdefault('govoo_technical_score', bid.govoo_technical_score)
            res.setdefault('govoo_financial_score', bid.govoo_financial_score)
        return res

    def action_submit(self):
        self.ensure_one()
        if not self.env.user.has_group('govoo_procurement.group_govoo_procurement_evaluator'):
            raise AccessError(_('Only a Procurement Evaluator can submit a bid score.'))
        self.bid_id.sudo().write({
            'govoo_technical_score': self.govoo_technical_score,
            'govoo_financial_score': self.govoo_financial_score,
        })
