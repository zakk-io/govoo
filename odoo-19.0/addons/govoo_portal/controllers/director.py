# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class DirectorPortal(CustomerPortal):

    def _get_guide_portal_bootstrapped(self):
        return True

    # ------------------------------------------------------------
    # My Meetings
    # ------------------------------------------------------------

    @http.route('/my/meetings', type='http', auth='user')
    def portal_my_meetings(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get committees this partner belongs to
        committee_ids = request.env['govoo.appointment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('role', '=', 'committee_member'),
            ('state', '=', 'active'),
        ]).mapped('committee_id')

        domain = [('committee_id', 'in', committee_ids.ids)]
        meeting_count = request.env['govoo.meeting'].sudo().search_count(domain)

        pager = portal_pager(
            url='/my/meetings',
            total=meeting_count,
            page=page,
            step=15,
            scope=5,
        )
        meetings = request.env['govoo.meeting'].sudo().search(
            domain,
            order='dateScheduled desc',
            limit=15,
            offset=pager['offset'],
        )
        values.update({
            'meetings': meetings,
            'page_name': 'meetings',
            'pager': pager,
            'default_url': '/my/meetings',
        })
        return request.render('govoo_portal.portal_my_meetings', values)

    @http.route('/my/meetings/<int:meeting_id>', type='http', auth='user')
    def portal_my_meeting(self, meeting_id, access_token=None, **kw):
        try:
            meeting_sudo = self._document_check_access(
                'govoo.meeting', meeting_id, access_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'meeting': meeting_sudo,
            'page_name': 'meeting',
            'token': access_token,
        }
        return request.render('govoo_portal.portal_my_meeting', values)

    # ------------------------------------------------------------
    # My Votes (Director)
    # ------------------------------------------------------------

    @http.route('/my/votes', type='http', auth='user')
    def portal_my_votes(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get committees this partner belongs to
        committee_ids = request.env['govoo.appointment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('role', '=', 'committee_member'),
            ('state', '=', 'active'),
        ]).mapped('committee_id')

        # Get open resolutions for meetings of these committees where user hasn't voted
        voted_resolution_ids = request.env['govoo.vote'].sudo().search([
            ('voter_id', '=', partner.id),
        ]).mapped('resolution_id').ids

        # Get meetings for the committees
        meetings = request.env['govoo.meeting'].sudo().search([
            ('committee_id', 'in', committee_ids.ids),
        ])

        domain = [
            ('state', '=', 'open'),
            ('meeting_id', 'in', meetings.ids),
            ('id', 'not in', voted_resolution_ids),
        ]
        resolution_count = request.env['govoo.resolution'].sudo().search_count(domain)

        pager = portal_pager(
            url='/my/votes',
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
            'page_name': 'votes',
            'pager': pager,
            'default_url': '/my/votes',
        })
        return request.render('govoo_portal.portal_my_votes', values)

    @http.route('/my/votes/<int:resolution_id>/cast', type='http',
                auth='user', methods=['GET', 'POST'])
    def portal_cast_vote_director(self, resolution_id, access_token=None,
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
                return request.render('govoo_portal.portal_cast_vote', values)

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
                return request.render('govoo_portal.portal_cast_vote', values)

            request.env['govoo.vote'].sudo().create({
                'resolution_id': resolution_id,
                'voter_id': partner.id,
                'choice': vote_choice,
                'is_conflicted': bool(conflict_declared),
            })
            return request.redirect('/my/votes')

        values = {
            'resolution': resolution_sudo,
            'page_name': 'cast_vote',
            'token': access_token,
        }
        return request.render('govoo_portal.portal_cast_vote', values)

    # ------------------------------------------------------------
    # My Appointment
    # ------------------------------------------------------------

    @http.route('/my/appointment', type='http', auth='user')
    def portal_my_appointment(self, **kw):
        partner = request.env.user.partner_id
        appointment = request.env['govoo.appointment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active'),
        ], limit=1)
        values = {
            'appointment': appointment,
            'page_name': 'appointment',
        }
        return request.render('govoo_portal.portal_my_appointment', values)
