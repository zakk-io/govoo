# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class GovooPortalMain(CustomerPortal):

    @http.route('/my', type='http', auth='user', website=True)
    def portal_my_home(self, **kw):
        """Override base CustomerPortal home route to avoid website dependency."""
        partner = request.env.user.partner_id
        values = {
            'partner': partner,
            'user': request.env.user,
            'page_name': 'home',
        }
        # Determine which portal type this user is
        user_group_names = [g.name for g in request.env.user.group_ids]
        if 'govoo_director_portal' in user_group_names:
            values['portal_type'] = 'director'
        elif 'govoo_shareholder_portal' in user_group_names:
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
