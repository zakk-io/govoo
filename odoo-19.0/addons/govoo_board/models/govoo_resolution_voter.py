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
        help='Auto-granted on resolution open when the voter has a usable '
             'email (issue #234) via the same "Grant Portal Access" '
             'mechanism as a manual grant. Stays False -- and the voter '
             'stays flagged below -- only when they have no email on '
             'file, or it already belongs to another account.',
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

    def action_grant_portal_access(self):
        """Auto-create portal access for this voter if they don't have it
        yet, by reusing Odoo's own "Grant Portal Access" flow
        (portal.wizard / portal.wizard.user) rather than hand-rolling
        res.users creation, signup-token prep, and the invite email --
        this is the exact same path a human clicking "Grant Portal
        Access" on the partner form would trigger, so it creates the
        user, sends them the standard "set your password" email, and
        leaves an audit trail the same way.

        A no-op when the voter already has access, or when their email is
        missing or already claimed by another account -- those are left
        flagged (has_portal_access stays False) rather than raised, so
        one bad email does not block granting access to every other
        voter on the same resolution.

        Runs as sudo: portal.wizard/res.users.group_ids are restricted to
        base.group_partner_manager / base.group_system in core Odoo, which
        the Company Secretary role calling action_open() does not need as
        a standing grant just for this one, narrowly-scoped action.
        """
        self.ensure_one()
        if self.has_portal_access or not self.partner_id.email:
            return
        wizard = self.env['portal.wizard'].sudo().create({
            'partner_ids': [(4, self.partner_id.id)],
        })
        wizard_user = wizard.user_ids.filtered(lambda u: u.partner_id == self.partner_id)
        if not wizard_user or wizard_user.email_state != 'ok':
            return
        wizard_user.action_grant_access()
        group_xmlid = (
            'govoo_base.group_govoo_shareholder_portal' if self.voter_type == 'shareholder'
            else 'govoo_base.group_govoo_director_portal'
        )
        wizard_user.user_id.group_ids = [(4, self.env.ref(group_xmlid).id)]
        # has_portal_access is a *stored* compute keyed only on partner_id
        # -- invalidating its cache just re-reads the (still-False) stored
        # column, since nothing about partner_id itself changed to trigger
        # the ORM's own dependency-based recompute. The grant above is a
        # real, just-confirmed external side effect, so set it directly
        # rather than relying on invalidate-then-reread to pick it up.
        self.has_portal_access = True
