# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooVote(models.Model):
    _name = 'govoo.vote'
    _description = 'Vote on Resolution'
    _order = 'create_date desc'

    _vote_unique_per_resolution_voter = models.Constraint(
        'unique(resolution_id, voter_id)',
        'Only one vote per voter per resolution.',
    )

    resolution_id = fields.Many2one(
        comodel_name='govoo.resolution',
        string='Resolution',
        required=True,
        ondelete='restrict',
    )
    voter_id = fields.Many2one(
        comodel_name='res.partner',
        string='Voter',
        required=True,
        ondelete='restrict',
    )
    choice = fields.Selection(
        selection=[
            ('for', 'For'),
            ('against', 'Against'),
            ('abstain', 'Abstain'),
        ],
        string='Vote',
        required=True,
    )
    weight = fields.Float(
        string='Vote Weight',
        required=True,
        default=1.0,
        help='1.0 per director; voting_power from govoo.share.holding for shareholder resolutions.',
    )
    is_conflicted = fields.Boolean(
        string='Conflicted',
        default=False,
        help='Declared interest — vote excluded from tally where governance rule requires.',
    )
    timestamp = fields.Datetime(
        string='Timestamp',
        readonly=True,
        copy=False,
    )
    cast_by_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cast By (Proxy)',
        help='Set when a registered proxy casts this vote on someone '
             "else's behalf. The vote always belongs to the person who "
             'delegated it -- weight and eligibility are based on them, '
             'never the proxy. Blank when the voter cast their own vote.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('timestamp'):
                vals['timestamp'] = fields.Datetime.now()
            # Auto-set weight from holdings for shareholder resolutions.
            # Delegated to govoo.resolution._compute_vote_weight_for so the
            # portal's pre-submit weight-disclosure preview (issue #269
            # item 2) can never drift from what actually gets stored here.
            if vals.get('resolution_id') and vals.get('voter_id') and 'weight' not in vals:
                resolution = self.env['govoo.resolution'].browse(vals['resolution_id'])
                voter = self.env['res.partner'].browse(vals['voter_id'])
                vals['weight'] = resolution._compute_vote_weight_for(voter)
        return super().create(vals_list)

    def write(self, vals):
        """Votes are immutable once timestamped."""
        if 'choice' in vals or 'weight' in vals or 'voter_id' in vals or 'cast_by_id' in vals:
            for rec in self:
                if rec.timestamp:
                    raise ValidationError(_('Votes are immutable once cast.'))
        return super().write(vals)

    @api.constrains('voter_id')
    def _check_voter_eligibility(self):
        """Board Administrator (no appointment) cannot vote (BR-SEC-004).

        This is enforced at the access-rights level (no create permission
        for group_govoo_admin), but we add a Python check as defense-in-depth.
        """
        for rec in self:
            if rec.voter_id:
                user = self.env['res.users'].search([
                    ('partner_id', '=', rec.voter_id.id),
                ], limit=1)
                if user and self.env.user.has_group('govoo_base.group_govoo_admin'):
                    # Check if the admin also has an active appointment (director/shareholder)
                    has_role = self.env['govoo.appointment'].search([
                        ('partner_id', '=', rec.voter_id.id),
                        ('state', '=', 'active'),
                    ], limit=1)
                    has_holding = self.env['govoo.share.holding'].search([
                        ('partner_id', '=', rec.voter_id.id),
                        ('quantity', '>', 0),
                    ], limit=1)
                    if not has_role and not has_holding:
                        raise ValidationError(
                            _('Board Administrator cannot vote without an active appointment '
                              'or shareholding (BR-SEC-004).')
                        )
