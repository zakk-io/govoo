# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shareholding_company_ids = fields.Many2many(
        comodel_name='res.company',
        string='Companies with a Shareholding',
        compute='_compute_shareholding_company_ids',
        help='Companies where this partner holds a nonzero quantity of '
             'shares in any class. Used to scope Shareholder Portal '
             'visibility to resolutions of companies they actually hold '
             'shares in (record-rules.md §4).',
    )

    def _compute_shareholding_company_ids(self):
        holdings = self.env['govoo.share.holding'].sudo().search([
            ('partner_id', 'in', self.ids),
            ('quantity', '>', 0),
        ])
        by_partner = {}
        for holding in holdings:
            by_partner.setdefault(holding.partner_id.id, set()).add(holding.company_id.id)
        for partner in self:
            company_ids = by_partner.get(partner.id, set())
            partner.shareholding_company_ids = [(6, 0, list(company_ids))]
