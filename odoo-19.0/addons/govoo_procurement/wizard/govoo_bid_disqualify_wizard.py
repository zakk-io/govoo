# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class GovooBidDisqualifyWizard(models.TransientModel):
    _name = 'govoo.bid.disqualify.wizard'
    _description = 'Disqualify a Vendor Bid (Pre-Evaluation)'

    bid_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Vendor Bid',
        required=True,
        readonly=True,
    )
    reason = fields.Text(
        string='Reason',
        required=True,
        help='Why this bid does not comply with the advertised '
             'requirements -- recorded on the bid itself (issue #328), '
             'not only in chatter.',
    )

    def action_submit(self):
        self.ensure_one()
        if self.bid_id.govoo_tender_id.evaluation_stage != 'pre_evaluation':
            raise ValidationError(_(
                'A bid can only be disqualified during Pre-Evaluation.'
            ))
        self.bid_id.write({
            'govoo_qualification_status': 'disqualified',
            'govoo_disqualification_reason': self.reason,
        })
