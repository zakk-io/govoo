# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class DirectorPortal(CustomerPortal):

    def _get_guide_portal_bootstrapped(self):
        return True

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
    # My Meetings
    # ------------------------------------------------------------

    @http.route('/my/meetings', type='http', auth='user', website=True)
    def portal_my_meetings(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get committees this partner belongs to. Any non-secretary role
        # (director/chair/md/committee_member) counts as membership, same
        # as govoo.committee.member_ids's own domain -- a Chairperson or
        # MD appointed directly to the Board (role='chair'/'md', not
        # 'committee_member') must still see their own Board meetings.
        committee_ids = request.env['govoo.appointment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('role', '!=', 'secretary'),
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
            order='date desc',
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

    @http.route('/my/meetings/<int:meeting_id>/pack', type='http', auth='user', website=True)
    def portal_my_meeting_pack(self, meeting_id, access_token=None, **kw):
        """Download the compiled board pack PDF -- gated on the same
        meeting access check as the meeting detail page itself, plus a
        check that this partner is an actual pack recipient (BR-SEC-006:
        no share-link-only bypass; being sent the pack is required, not
        just being able to read the meeting)."""
        try:
            meeting_sudo = self._document_check_access(
                'govoo.meeting', meeting_id, access_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        partner = request.env.user.partner_id
        if not meeting_sudo.pack_id or not meeting_sudo.pack_id.document_id:
            return request.redirect('/my/meetings/%d?access_token=%s' % (meeting_id, access_token or ''))
        recipient = request.env['govoo.board.pack.recipient'].sudo().search([
            ('pack_id', '=', meeting_sudo.pack_id.id),
            ('partner_id', '=', partner.id),
        ], limit=1)
        if not recipient:
            return request.redirect('/my/meetings/%d?access_token=%s' % (meeting_id, access_token or ''))

        stream = request.env['ir.binary']._get_stream_from(
            meeting_sudo.pack_id.document_id, filename_field='name',
        )
        return stream.get_response(as_attachment=True)

    @http.route('/my/meetings/<int:meeting_id>', type='http', auth='user', website=True)
    def portal_my_meeting(self, meeting_id, access_token=None, **kw):
        try:
            meeting_sudo = self._document_check_access(
                'govoo.meeting', meeting_id, access_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        partner = request.env.user.partner_id
        pack_recipient_sudo = None
        if meeting_sudo.pack_id:
            pack_recipient_sudo = request.env['govoo.board.pack.recipient'].sudo().search([
                ('pack_id', '=', meeting_sudo.pack_id.id),
                ('partner_id', '=', partner.id),
            ], limit=1)

        values = {
            'meeting': meeting_sudo,
            'pack_recipient': pack_recipient_sudo,
            'page_name': 'meeting',
            'token': access_token,
        }
        return request.render('govoo_portal.portal_my_meeting', values)

    # ------------------------------------------------------------
    # My Votes (Director)
    # ------------------------------------------------------------

    @http.route('/my/votes', type='http', auth='user', website=True)
    def portal_my_votes(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get committees this partner belongs to (see portal_my_meetings
        # for why 'role != secretary' rather than just 'committee_member').
        committee_ids = request.env['govoo.appointment'].sudo().search([
            ('partner_id', '=', partner.id),
            ('role', '!=', 'secretary'),
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
                auth='user', methods=['GET', 'POST'], website=True)
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

    @http.route('/my/appointment', type='http', auth='user', website=True)
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
