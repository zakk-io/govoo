# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class ProcurementCommitteePortal(CustomerPortal):
    """Issue #333: read-only, committee-scoped portal access for
    external/extra Procurement Committee members -- mirrors
    DirectorPortal (director.py) exactly, reusing the same
    sudo-then-check_access security pattern (BR-SEC-006: no
    token-only bypass) rather than inventing a variant. Deliberately
    has no routes that write anything -- scoring stays on the existing
    internal Evaluator wizard (see #333's own acceptance criteria)."""

    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.with_user(SUPERUSER_ID).exists()
        if not document_sudo:
            raise MissingError(_('This document does not exist.'))
        document.check_access('read')
        return document_sudo

    @http.route('/my/procurement/tenders', type='http', auth='user', website=True)
    def portal_my_procurement_tenders(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        committee_ids = request.env['govoo.appointment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('role', '!=', 'secretary'),
            ('state', '=', 'active'),
        ]).mapped('committee_id')

        # Issue #337: a tender's Technical and Financial Evaluation are
        # separate meetings/committees -- in scope via either one.
        domain = ['|',
            ('technical_evaluation_meeting_id.committee_id', 'in', committee_ids.ids),
            ('financial_evaluation_meeting_id.committee_id', 'in', committee_ids.ids),
        ]
        tender_count = request.env['govoo.tender'].sudo().search_count(domain)

        pager = portal_pager(
            url='/my/procurement/tenders',
            total=tender_count,
            page=page,
            step=15,
            scope=5,
        )
        tenders = request.env['govoo.tender'].sudo().search(
            domain,
            order='create_date desc',
            limit=15,
            offset=pager['offset'],
        )
        values.update({
            'tenders': tenders,
            'page_name': 'procurement_tenders',
            'pager': pager,
            'default_url': '/my/procurement/tenders',
        })
        return request.render('govoo_portal.portal_my_procurement_tenders', values)

    @http.route('/my/procurement/tenders/<int:tender_id>', type='http', auth='user', website=True)
    def portal_my_procurement_tender(self, tender_id, access_token=None, **kw):
        try:
            tender_sudo = self._document_check_access(
                'govoo.tender', tender_id, access_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'tender': tender_sudo,
            'page_name': 'procurement_tender',
            'token': access_token,
        }
        return request.render('govoo_portal.portal_my_procurement_tender', values)
