# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.exceptions import AccessError


class GovooTenderAwardWizard(models.TransientModel):
    _name = 'govoo.tender.award.wizard'
    _description = 'Confirm the Awarded Bid and Award a Tender'

    tender_id = fields.Many2one(
        comodel_name='govoo.tender',
        string='Tender',
        required=True,
        readonly=True,
    )
    awarded_bid_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Awarded Bid',
        required=True,
        domain="[('govoo_tender_id', '=', tender_id)]",
    )

    def action_submit(self):
        self.ensure_one()
        if not self.env.user.has_group('govoo_procurement.group_govoo_procurement_approver'):
            raise AccessError(_('Only a Procurement Approver can award a tender.'))
        tender = self.tender_id.sudo()
        tender.write({'awarded_bid_id': self.awarded_bid_id.id})
        tender.action_award()
