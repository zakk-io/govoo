# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class ShareholderPortal(CustomerPortal):

    def _document_check_access(self, model_name, document_id, access_token=None):
        """Record rule only -- no token-only fallback (BR-SEC-006).

        Governance records are never share-link-shareable: an
        authenticated portal user who isn't authorized for a record
        must stay blocked even with a valid/leaked access token.
        """
        document = request.env[model_name].browse([document_id])
        document_sudo = document.with_user(SUPERUSER_ID).exists()
        if not document_sudo:
            raise MissingError(_('This document does not exist.'))
        document.check_access('read')
        return document_sudo

    # ------------------------------------------------------------
    # My Holdings
    # ------------------------------------------------------------

    @http.route('/my/holdings', type='http', auth='user', website=True)
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

    @http.route('/my/holdings/votes', type='http', auth='user', website=True)
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
            'proxy_items': self._get_proxy_vote_items(partner, voter_type='shareholder'),
            'page_name': 'shareholder_votes',
            'pager': pager,
            'default_url': '/my/holdings/votes',
        })
        return request.render('govoo_portal.portal_my_shareholder_votes', values)

    def _get_proxy_vote_items(self, proxy_partner, voter_type):
        """Issue #269 item 1: see DirectorPortal._get_proxy_vote_items --
        duplicated rather than shared because DirectorPortal and
        ShareholderPortal are two independent CustomerPortal subclasses
        with no common base of their own, same as _document_check_access
        above is already duplicated between the two."""
        proxies = request.env['govoo.vote.proxy']._get_active_proxies_for(proxy_partner.id)
        items = []
        for proxy in proxies:
            principal = proxy.principal_partner_id
            resolutions = request.env['govoo.resolution'].sudo().search([
                ('state', '=', 'open'),
                ('meeting_id', '=', proxy.meeting_id.id),
            ])
            for resolution in resolutions:
                already_voted = request.env['govoo.vote'].sudo().search_count([
                    ('resolution_id', '=', resolution.id),
                    ('voter_id', '=', principal.id),
                ])
                if already_voted:
                    continue
                voter_row = resolution.voter_notification_ids.filtered(
                    lambda v, p=principal: v.partner_id == p,
                )
                if voter_row and voter_row[0].voter_type == voter_type:
                    items.append({'resolution': resolution, 'principal': principal})
        return items

    @http.route('/my/holdings/votes/<int:resolution_id>/cast', type='http',
                auth='user', methods=['GET', 'POST'], website=True)
    def portal_cast_vote_shareholder(self, resolution_id, access_token=None,
                                     vote_choice=None, conflict_declared=None,
                                     on_behalf_of=None, confirmed=None, **kw):
        try:
            resolution_sudo = self._document_check_access(
                'govoo.resolution', resolution_id, access_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        partner = request.env.user.partner_id
        voter_partner, on_behalf_of = self._resolve_vote_voter(
            partner, resolution_sudo, on_behalf_of,
        )
        # Issue #269 item 2: weight is now always sourced the same way
        # govoo.vote.create() itself sources it (resolution._compute_vote_
        # weight_for), rather than this controller separately summing every
        # holding -- the two could previously disagree for a shareholder
        # holding more than one share class. This is also what the
        # pre-submit disclosure preview below must show.
        weight = resolution_sudo._compute_vote_weight_for(voter_partner)

        base_values = {
            'resolution': resolution_sudo,
            'page_name': 'cast_vote',
            'token': access_token,
            'weight': weight,
            'on_behalf_of': on_behalf_of,
            'principal_name': voter_partner.name if on_behalf_of else None,
        }

        if request.httprequest.method == 'POST':
            if not vote_choice:
                values = dict(base_values, error=_('Please select a vote choice.'))
                return request.render('govoo_portal.portal_cast_vote_shareholder', values)

            # Check for existing vote
            existing = request.env['govoo.vote'].sudo().search([
                ('resolution_id', '=', resolution_id),
                ('voter_id', '=', voter_partner.id),
            ], limit=1)
            if existing:
                values = dict(base_values, error=_('This voter has already voted on this resolution.'))
                return request.render('govoo_portal.portal_cast_vote_shareholder', values)

            if not confirmed:
                values = dict(
                    base_values,
                    confirm_step=True,
                    selected_choice=vote_choice,
                    selected_conflict=bool(conflict_declared),
                )
                return request.render('govoo_portal.portal_cast_vote_shareholder', values)

            create_vals = {
                'resolution_id': resolution_id,
                'voter_id': voter_partner.id,
                'choice': vote_choice,
                'is_conflicted': bool(conflict_declared),
            }
            if on_behalf_of:
                create_vals['cast_by_id'] = partner.id
            request.env['govoo.vote'].sudo().create(create_vals)
            return request.redirect('/my/holdings/votes')

        return request.render('govoo_portal.portal_cast_vote_shareholder', base_values)

    def _resolve_vote_voter(self, current_partner, resolution_sudo, on_behalf_of):
        """Issue #269 item 1: see DirectorPortal._resolve_vote_voter --
        duplicated for the same reason as _get_proxy_vote_items above."""
        if not on_behalf_of:
            return current_partner, None
        try:
            principal_id = int(on_behalf_of)
        except (TypeError, ValueError):
            return current_partner, None
        is_valid_proxy = request.env['govoo.vote.proxy']._is_active_proxy_for(
            current_partner.id, principal_id, resolution_sudo.meeting_id.id,
        )
        if not is_valid_proxy:
            return current_partner, None
        principal = request.env['res.partner'].sudo().browse(principal_id).exists()
        if not principal:
            return current_partner, None
        return principal, principal_id

    # ------------------------------------------------------------
    # My Register Entry
    # ------------------------------------------------------------

    @http.route('/my/register', type='http', auth='user', website=True)
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
