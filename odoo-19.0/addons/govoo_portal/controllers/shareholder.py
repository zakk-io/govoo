# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class ShareholderPortal(CustomerPortal):

    # ------------------------------------------------------------
    # My Holdings
    # ------------------------------------------------------------

    @http.route('/my/holdings', type='http', auth='user')
    def portal_my_holdings(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', '=', partner.id)]
        holding_count = request.env['govoo.share.holding'].sudo().search_count(domain)

        pager = portal_pager(
            url='/my/holdings',
            total=holding_count,
            page=page,
            step=15,
            scope=5,
        )
        holdings = request.env['govoo.share.holding'].sudo().search(
            domain,
            order='share_class_id, percentage desc',
            limit=15,
            offset=pager['offset'],
        )
        values.update({
            'holdings': holdings,
            'page_name': 'holdings',
            'pager': pager,
            'default_url': '/my/holdings',
        })
        return request.render('govoo_portal.portal_my_holdings', values)

    # ------------------------------------------------------------
    # My Votes (Shareholder)
    # ------------------------------------------------------------

    @http.route('/my/holdings/votes', type='http', auth='user')
    def portal_my_shareholder_votes(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get shareholder-type resolutions where user hasn't voted
        voted_resolution_ids = request.env['govoo.vote'].sudo().search([
            ('voter_id', '=', partner.id),
        ]).mapped('resolution_id').ids

        domain = [
            ('state', '=', 'open'),
            ('resolution_type', 'in', ('ordinary', 'special')),
            ('id', 'not in', voted_resolution_ids),
        ]
        resolution_count = request.env['govoo.resolution'].sudo().search_count(domain)

        pager = portal_pager(
            url='/my/holdings/votes',
            total=resolution_count,
            page=page,
            step=15,
            scope=5,
        )
        resolutions = request.env['govoo.resolution'].sudo().search(
            domain,
            order='create_date desc',
            limit=15,
            offset=pager['offset'],
        )
        values.update({
            'resolutions': resolutions,
            'page_name': 'shareholder_votes',
            'pager': pager,
            'default_url': '/my/holdings/votes',
        })
        return request.render('govoo_portal.portal_my_shareholder_votes', values)

    @http.route('/my/holdings/votes/<int:resolution_id>/cast', type='http',
                auth='user', methods=['GET', 'POST'])
    def portal_cast_vote_shareholder(self, resolution_id, access_token=None,
                                     vote_choice=None, conflict_declared=None, **kw):
        try:
            resolution_sudo = self._document_check_access(
                'govoo.resolution', resolution_id, access_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        partner = request.env.user.partner_id

        if request.httprequest.method == 'POST':
            if not vote_choice:
                values = {
                    'resolution': resolution_sudo,
                    'error': _('Please select a vote choice.'),
                    'page_name': 'cast_vote',
                    'token': access_token,
                }
                return request.render('govoo_portal.portal_cast_vote_shareholder', values)

            # Check for existing vote
            existing = request.env['govoo.vote'].sudo().search([
                ('resolution_id', '=', resolution_id),
                ('voter_id', '=', partner.id),
            ], limit=1)
            if existing:
                values = {
                    'resolution': resolution_sudo,
                    'error': _('You have already voted on this resolution.'),
                    'page_name': 'cast_vote',
                    'token': access_token,
                }
                return request.render('govoo_portal.portal_cast_vote_shareholder', values)

            # Get voting power from holdings
            holdings = request.env['govoo.share.holding'].sudo().search([
                ('partner_id', '=', partner.id),
            ])
            voting_power = sum(holdings.mapped('voting_power'))

            request.env['govoo.vote'].sudo().create({
                'resolution_id': resolution_id,
                'voter_id': partner.id,
                'choice': vote_choice,
                'weight': voting_power,
                'is_conflicted': bool(conflict_declared),
            })
            return request.redirect('/my/holdings/votes')

        values = {
            'resolution': resolution_sudo,
            'page_name': 'cast_vote',
            'token': access_token,
        }
        return request.render('govoo_portal.portal_cast_vote_shareholder', values)

    # ------------------------------------------------------------
    # My Register Entry
    # ------------------------------------------------------------

    @http.route('/my/register', type='http', auth='user')
    def portal_my_register(self, **kw):
        partner = request.env.user.partner_id
        register_entry = request.env['govoo.register.member'].sudo().search([
            ('partner_id', '=', partner.id),
        ], limit=1)
        values = {
            'register_entry': register_entry,
            'page_name': 'register',
        }
        return request.render('govoo_portal.portal_my_register', values)
