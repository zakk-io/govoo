# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class GovooFeatureFlags(models.AbstractModel):
    """Shared runtime detection for optional Enterprise apps (Documents,
    Sign) that several govoo_* modules degrade gracefully without.

    A Many2one field's comodel is fixed at class-definition time, so no
    field can dynamically repoint between ir.attachment and
    documents.document/sign.request per-install. The pattern this
    enables instead: keep the field as ir.attachment (always works,
    Community-safe), and when the richer app is installed, additionally
    create/link the companion documents.document/sign.request record at
    the point a document is actually generated.
    """
    _name = 'govoo.feature.flags'
    _description = 'Govoo Optional-App Feature Detection'

    @api.model
    def is_documents_app_installed(self):
        """Whether the Documents app (Enterprise) is installed."""
        return bool(self.env['ir.module.module'].sudo().search_count([
            ('name', '=', 'documents'),
            ('state', '=', 'installed'),
        ]))

    @api.model
    def is_sign_app_installed(self):
        """Whether the Sign app (Enterprise) is installed."""
        return bool(self.env['ir.module.module'].sudo().search_count([
            ('name', '=', 'sign'),
            ('state', '=', 'installed'),
        ]))
