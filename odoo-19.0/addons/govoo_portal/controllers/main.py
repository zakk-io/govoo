# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class GovooPortalMain(CustomerPortal):

    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kw):
        """Override CustomerPortal.home() -- same method name is required for
        Odoo's controller inheritance to actually replace the parent's route
        (a differently-named method registers as a competing rule for the
        same URLs instead of overriding it)."""
        partner = request.env.user.partner_id
        values = {
            'partner': partner,
            'user': request.env.user,
            'page_name': 'home',
        }
        # Determine which portal type this user is
        user = request.env.user
        if user.has_group('govoo_base.group_govoo_director_portal'):
            values['portal_type'] = 'director'
        elif user.has_group('govoo_base.group_govoo_shareholder_portal'):
            values['portal_type'] = 'shareholder'
        else:
            values['portal_type'] = 'internal'
        return request.render('govoo_portal.portal_home', values)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'meeting_count' in counters:
            values['meeting_count'] = self._get_meeting_count(partner)
        if 'resolution_count' in counters:
            values['resolution_count'] = self._get_resolution_count(partner)
        if 'holding_count' in counters:
            values['holding_count'] = self._get_holding_count(partner)
        return values

    def _get_meeting_count(self, partner):
        """Count meetings for committees the portal user belongs to."""
        committee_ids = request.env['govoo.appointment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('role', '=', 'committee_member'),
            ('state', '=', 'active'),
        ]).mapped('committee_id')
        if not committee_ids:
            return 0
        return request.env['govoo.meeting'].sudo().search_count([
            ('committee_id', 'in', committee_ids.ids),
        ])

    def _get_resolution_count(self, partner):
        """Count open resolutions the portal user is eligible to vote on."""
        # Only count shareholder-type resolutions where user has holdings
        has_holdings = request.env['govoo.share.holding'].sudo().search_count([
            ('partner_id', '=', partner.id),
        ])
        if not has_holdings:
            return 0
        # Exclude resolutions already voted on
        voted_ids = request.env['govoo.vote'].sudo().search([
            ('voter_id', '=', partner.id),
        ]).mapped('resolution_id').ids
        return request.env['govoo.resolution'].sudo().search_count([
            ('state', '=', 'open'),
            ('resolution_type', 'in', ('ordinary', 'special')),
            ('id', 'not in', voted_ids),
        ])

    def _get_holding_count(self, partner):
        """Count share holdings for the portal user."""
        return request.env['govoo.share.holding'].sudo().search_count([
            ('partner_id', '=', partner.id),
        ])
