# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooVoteProxy(models.Model):
    """Issue #269 item 1: proxy voting appointment. principal_partner_id
    delegates voting authority for every resolution tied to one meeting to
    proxy_partner_id -- the same shape a real AGM/board proxy form takes
    (one appointment covers a whole meeting, not one resolution at a
    time), rather than a per-resolution grant.

    v1 is Secretary/Admin-administered only (backend form): there is no
    portal self-service appointment flow yet -- called out explicitly as
    out of scope for this pass in issue #269, not silently missing.
    """

    _name = 'govoo.vote.proxy'
    _description = 'Voting Proxy Appointment'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    _proxy_unique_per_meeting = models.Constraint(
        'unique(principal_partner_id, meeting_id)',
        'A principal may only appoint one proxy per meeting.',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    meeting_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Meeting',
        required=True,
        ondelete='cascade',
        check_company=True,
        tracking=True,
        help='Covers every resolution linked to this meeting -- matches '
             'how a real AGM/board proxy form is scoped.',
    )
    principal_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Principal (Delegating Voter)',
        required=True,
        tracking=True,
        help='The director or shareholder who is delegating their vote.',
    )
    proxy_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Proxy (Casts the Vote)',
        required=True,
        tracking=True,
        help="The person who will actually cast the vote on the principal's "
             'behalf.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
    )

    @api.depends('principal_partner_id.name', 'proxy_partner_id.name', 'meeting_id.name')
    def _compute_display_name(self):
        # No plain-text field on this model, so display_name would
        # otherwise fall back to the raw "govoo.vote.proxy,<id>" string.
        for rec in self:
            if rec.principal_partner_id and rec.proxy_partner_id:
                rec.display_name = '%s → %s (%s)' % (
                    rec.principal_partner_id.name,
                    rec.proxy_partner_id.name,
                    rec.meeting_id.name or _('no meeting'),
                )
            else:
                rec.display_name = _('Voting Proxy')

    @api.constrains('principal_partner_id', 'proxy_partner_id')
    def _check_not_self_proxy(self):
        for rec in self:
            if rec.principal_partner_id == rec.proxy_partner_id:
                raise ValidationError(_('A voter cannot be their own proxy.'))

    @api.model
    def _get_active_proxies_for(self, proxy_partner_id):
        """Every active appointment naming proxy_partner_id as the proxy --
        used by the portal (director.py/shareholder.py) to surface
        resolutions the current user can cast on someone else's behalf.
        Runs as sudo: the portal user has no direct read access to this
        model (see ir.model.access.csv), matching the sudo() pattern
        already used throughout govoo_portal's controllers."""
        return self.sudo().search([
            ('proxy_partner_id', '=', proxy_partner_id),
            ('active', '=', True),
        ])

    def _is_active_proxy_for(self, proxy_partner_id, principal_partner_id, meeting_id):
        """True iff an active proxy.sudo() row grants proxy_partner_id the
        right to cast votes for principal_partner_id on meeting_id."""
        return bool(self.sudo().search_count([
            ('proxy_partner_id', '=', proxy_partner_id),
            ('principal_partner_id', '=', principal_partner_id),
            ('meeting_id', '=', meeting_id),
            ('active', '=', True),
        ]))
