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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('timestamp'):
                vals['timestamp'] = fields.Datetime.now()
            # Auto-set weight from holdings for shareholder resolutions.
            # 'ordinary'/'special' resolution_type is also used for
            # regular board-meeting resolutions (not just shareholder
            # ones), so resolution_type alone isn't a sufficient
            # signal: a director who happens to also be a shareholder
            # must still get a plain 1.0 vote on a board resolution,
            # not their shareholder voting_power. Source from holdings
            # when either the meeting is genuinely shareholder-type
            # (agm/egm) or there's no meeting at all (a written
            # resolution, meeting_id is nullable per relationships.md
            # §1) -- the latter is the gap this fixes. 'ordinary'/
            # 'special' as the shareholder-eligible resolution_type set
            # matches the same [CONFIRM] mapping already adopted by
            # govoo_resolution_shareholder_portal_rule (record-rules.md §4).
            if vals.get('resolution_id') and vals.get('voter_id'):
                resolution = self.env['govoo.resolution'].browse(vals['resolution_id'])
                voter = self.env['res.partner'].browse(vals['voter_id'])
                is_shareholder_eligible_type = resolution.resolution_type in ('ordinary', 'special')
                is_shareholder_meeting_context = (
                    not resolution.meeting_id
                    or resolution.meeting_id.meeting_type in ('agm', 'egm')
                )
                if is_shareholder_eligible_type and is_shareholder_meeting_context:
                    # Shareholder resolution — source weight from holdings.
                    # resolution.company_id is related='meeting_id.company_id'
                    # and therefore False for a written (meeting-less)
                    # resolution -- fall back to the current company so
                    # the holding lookup still works for that case.
                    company_id = resolution.company_id.id or self.env.company.id
                    holding = self.env['govoo.share.holding'].search([
                        ('partner_id', '=', voter.id),
                        ('company_id', '=', company_id),
                    ], limit=1)
                    if holding:
                        vals['weight'] = holding.voting_power
        return super().create(vals_list)

    def write(self, vals):
        """Votes are immutable once timestamped."""
        if 'choice' in vals or 'weight' in vals or 'voter_id' in vals:
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
