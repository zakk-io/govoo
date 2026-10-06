# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_governance_secretary_partners(self, extra_partner=None):
        """Every active Company Secretary's partner, for reminder emails that
        must always reach secretarial oversight regardless of whatever
        specific responsible person a record may also have (issue #236).
        `extra_partner` (e.g. an obligation's responsible_id.partner_id) is
        folded in too, deduplicated, if given and has an email.
        """
        secretaries = self.sudo().search([
            ('group_ids', 'in', self.env.ref('govoo_base.group_govoo_secretary').id),
            ('active', '=', True),
        ]).mapped('partner_id').filtered('email')
        if extra_partner and extra_partner.email and extra_partner not in secretaries:
            secretaries |= extra_partner
        return secretaries
