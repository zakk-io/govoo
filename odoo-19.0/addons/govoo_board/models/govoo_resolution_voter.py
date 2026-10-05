# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class GovooResolutionVoter(models.Model):
    """One row per eligible voter notified when a resolution opens (issue
    #234) -- same shape and purpose as govoo.board.pack.recipient
    (govoo_board_pack.py): a distribution/notification log, not an
    independently-edited business record, so it skips mail.thread per the
    same audit-trail exception already applied there.
    """

    _name = 'govoo.resolution.voter'
    _description = 'Resolution Voting Notification Recipient'

    resolution_id = fields.Many2one(
        comodel_name='govoo.resolution',
        string='Resolution',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Voter',
        required=True,
    )
    voter_type = fields.Selection(
        selection=[
            ('director', 'Director'),
            ('shareholder', 'Shareholder'),
        ],
        string='Voter Type',
        required=True,
    )
    has_portal_access = fields.Boolean(
        string='Has Portal Access',
        compute='_compute_has_portal_access',
        store=True,
        help='False means this voter has no active portal login yet, so '
             'the voting-invite email was not sent -- they are skipped '
             'and flagged here rather than auto-provisioned (issue #234).',
    )
    portal_url = fields.Char(
        string='Voting Link',
        compute='_compute_portal_url',
    )
    notified_date = fields.Datetime(
        string='Notified On',
    )

    @api.depends('partner_id')
    def _compute_has_portal_access(self):
        for rec in self:
            user = self.env['res.users'].sudo().search([
                ('partner_id', '=', rec.partner_id.id),
                ('active', '=', True),
            ], limit=1)
            rec.has_portal_access = bool(user)

    @api.depends('voter_type', 'resolution_id')
    def _compute_portal_url(self):
        # Director and shareholder votes are cast on two different portal
        # routes (govoo_portal's director.py vs shareholder.py) -- a
        # single generic link (e.g. govoo.resolution's own
        # _compute_access_url, hardcoded to the director route) cannot
        # correctly address both, which is exactly why this is computed
        # per voter row instead.
        for rec in self:
            if rec.voter_type == 'shareholder':
                rec.portal_url = '/my/holdings/votes/%s/cast' % rec.resolution_id.id
            else:
                rec.portal_url = '/my/votes/%s/cast' % rec.resolution_id.id
