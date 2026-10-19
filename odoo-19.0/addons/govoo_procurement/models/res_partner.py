# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models
from odoo.exceptions import AccessError

_GOVOO_GOVERNANCE_ROLE_FIELDS = (
    'govoo_is_director',
    'govoo_is_shareholder',
    'govoo_is_officer',
    'govoo_is_beneficial_owner',
)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _check_officer_not_changing_governance_role(self, vals):
        """A Procurement Officer can manage a vendor's ordinary contact
        details (granted write access in #314), but must never change a
        company's governance role classification -- that's the Company
        Secretary/Board Administrator's call, not procurement's. The view
        already renders these fields readonly for the Officer; this is
        the server-side guarantee that holds even for a direct write call
        bypassing the UI."""
        if any(field_name in vals for field_name in _GOVOO_GOVERNANCE_ROLE_FIELDS):
            if self.env.user.has_group('govoo_procurement.group_govoo_procurement_officer'):
                raise AccessError(_(
                    'Procurement Officers cannot change a company\'s governance '
                    'role classification. Ask a Company Secretary or Board '
                    'Administrator instead.'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_officer_not_changing_governance_role(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._check_officer_not_changing_governance_role(vals)
        return super().write(vals)
