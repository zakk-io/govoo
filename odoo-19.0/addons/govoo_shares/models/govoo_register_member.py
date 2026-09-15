# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GovooRegisterMember(models.Model):
    """Extends govoo.register.member (govoo_secretarial) with a link
    back to the shareholder's actual per-share-class holdings. Lives
    here rather than in govoo_secretarial since govoo_shares already
    depends on govoo_secretarial, not the reverse.
    """
    _inherit = 'govoo.register.member'

    holding_ids = fields.One2many(
        comodel_name='govoo.share.holding',
        string='Holdings',
        compute='_compute_holding_ids',
        help='This member\'s current per-share-class holdings. Virtual '
             '(not stored) -- there is no direct FK from govoo.share.holding '
             'to this register, so it is derived by partner + company.',
    )

    def _compute_holding_ids(self):
        for rec in self:
            rec.holding_ids = self.env['govoo.share.holding'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('company_id', '=', rec.company_id.id),
            ])
