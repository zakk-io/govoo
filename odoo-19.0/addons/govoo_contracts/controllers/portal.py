# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class ContractPortal(CustomerPortal):
    """Contract Viewer Portal ("My Contracts" area) -- ui/portal-ui.md
    section 2b. Standalone routes, not wired into govoo_portal's shared
    /my home page in this PR: that page dispatches on a fixed
    director/shareholder/internal portal_type and doesn't call super(),
    so extending it safely is a separate, later change, not bundled in
    here to avoid coupling two independently-tested modules.
    """

    def _document_check_access(self, model_name, document_id, access_token=None):
        """Record rule only -- no token-only fallback (BR-SEC-006), same
        discipline as govoo_portal's own DirectorPortal/
        ShareholderPortal controllers."""
        document = request.env[model_name].browse([document_id])
        document_sudo = document.with_user(SUPERUSER_ID).exists()
        if not document_sudo:
            raise MissingError(_('This document does not exist.'))
        document.check_access('read')
        return document_sudo

    @http.route('/my/contracts', type='http', auth='user', website=True)
    def portal_my_contracts(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [
            '|',
            ('counterparty_id', '=', partner.id),
            ('portal_approver_ids', 'in', partner.id),
        ]
        contract_count = request.env['govoo.contract'].sudo().search_count(domain)

        pager = portal_pager(
            url='/my/contracts',
            total=contract_count,
            page=page,
            step=15,
            scope=5,
        )
        contracts = request.env['govoo.contract'].sudo().search(
            domain,
            order='create_date desc',
            limit=15,
            offset=pager['offset'],
        )
        values.update({
            'contracts': contracts,
            'page_name': 'contracts',
            'pager': pager,
            'default_url': '/my/contracts',
        })
        return request.render('govoo_contracts.portal_my_contracts', values)

    @http.route('/my/contracts/<int:contract_id>', type='http', auth='user', website=True)
    def portal_my_contract(self, contract_id, access_token=None, **kw):
        try:
            contract_sudo = self._document_check_access(
                'govoo.contract', contract_id, access_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'contract': contract_sudo,
            'page_name': 'contract',
            'token': access_token,
        }
        return request.render('govoo_contracts.portal_my_contract', values)
