# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Issue #238: a single editable page for the [CONFIRM] legal thresholds that,
# before this model existed, were only reachable via Settings > Technical >
# System Parameters. Each field here mirrors one ir.config_parameter key that
# other modules already read directly (govoo_secretarial's and govoo_shares'
# reminder crons, govoo_board's own e-signature/retention checks) -- this
# model does not replace that storage, it is a secretary-friendly, tracked
# front-end for it. Lives in govoo_board (not govoo_secretarial/govoo_shares,
# which actually own four of these six parameters) because it is the only
# module in the base -> secretarial -> shares -> board dependency chain that
# can see all three modules' parameters at once.
_CONFIG_PARAMETER_FIELDS = {
    # field_name: (ir.config_parameter key, field type, clearable-at-zero)
    'charge_registration_deadline_days': (
        'govoo_secretarial.charge_registration_deadline_days', 'integer', True,
    ),
    'beneficial_owner_declaration_deadline_days': (
        'govoo_secretarial.beneficial_owner_declaration_deadline_days', 'integer', True,
    ),
    'certificate_issuance_deadline_days': (
        'govoo_shares.certificate_issuance_deadline_days', 'integer', True,
    ),
    'transfer_registration_deadline_days': (
        'govoo_shares.transfer_registration_deadline_days', 'integer', True,
    ),
    'e_signature_legally_confirmed': (
        'govoo_board.e_signature_legally_confirmed', 'boolean', False,
    ),
    'minutes_retention_default_years': (
        'govoo_board.minutes_retention_default_years', 'integer', False,
    ),
    # Issue #269: these five were previously only reachable via
    # Settings > Technical > System Parameters (special_resolution_
    # majority_threshold already existed and was read by govoo_resolution.py
    # -- this UI gap was found during the issue #269 audit, not introduced
    # by it). All five are new voting-workflow policy switches; every one
    # defaults to unset/disabled, per the same convention as the six above.
    'special_resolution_majority_threshold': (
        'govoo_board.special_resolution_majority_threshold', 'float', True,
    ),
    'resolution_voting_window_days': (
        'govoo_board.resolution_voting_window_days', 'integer', True,
    ),
    'resolution_notice_period_days': (
        'govoo_board.resolution_notice_period_days', 'integer', True,
    ),
    'resolution_meeting_state_gate_enabled': (
        'govoo_board.resolution_meeting_state_gate_enabled', 'boolean', False,
    ),
    'resolution_tie_break_enabled': (
        'govoo_board.resolution_tie_break_enabled', 'boolean', False,
    ),
    'written_resolution_quorum_percentage': (
        'govoo_board.written_resolution_quorum_percentage', 'float', True,
    ),
    # Issue #271: meeting/minutes/board-pack workflow policy switches,
    # same unset-by-default convention.
    'meeting_notice_period_days': (
        'govoo_board.meeting_notice_period_days', 'integer', True,
    ),
    'minutes_require_different_approver': (
        'govoo_board.minutes_require_different_approver', 'boolean', False,
    ),
    'board_pack_min_lead_days': (
        'govoo_board.board_pack_min_lead_days', 'integer', True,
    ),
    'agenda_freeze_on_schedule': (
        'govoo_board.agenda_freeze_on_schedule', 'boolean', False,
    ),
    'meeting_close_requires_minutes_approved': (
        'govoo_board.meeting_close_requires_minutes_approved', 'boolean', False,
    ),
}


class GovooGovernanceConfig(models.Model):
    _name = 'govoo.governance.config'
    _description = 'Governance Configuration'
    _inherit = ['mail.thread']

    _company_uniq = models.Constraint(
        'unique(company_id)',
        'Only one Governance Configuration record is allowed per company.',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    # Statutory deadline fields below: exact day-counts are open legal
    # questions pending confirmation from the company's lawyers (company
    # articles / Rwandan law) -- see docs/spec/decisions/open-decisions.md.
    # 0 is the safe default: it leaves the corresponding reminder/check
    # disabled rather than guessing a number.
    charge_registration_deadline_days = fields.Integer(
        string='Charge Registration Deadline (days)',
        tracking=True,
        help="How many days after a charge is created it must be registered "
             "with the Registrar, before it risks being void against a "
             "liquidator or creditors. Leave at 0 to turn the reminder off "
             "until this is confirmed with your legal team.",
    )
    beneficial_owner_declaration_deadline_days = fields.Integer(
        string='Beneficial Owner Declaration Deadline (days)',
        tracking=True,
        help="How many days after someone becomes a registrable beneficial "
             "owner they must be declared/filed. Leave at 0 to turn the "
             "reminder off until this is confirmed with your legal team.",
    )
    certificate_issuance_deadline_days = fields.Integer(
        string='Share Certificate Issuance Deadline (days)',
        tracking=True,
        help="How many days after allotment a share certificate must be "
             "issued to the shareholder. Leave at 0 to turn the reminder "
             "off until this is confirmed with your legal team.",
    )
    transfer_registration_deadline_days = fields.Integer(
        string='Share Transfer Registration Deadline (days)',
        tracking=True,
        help="How many days after a transfer a share transfer must be "
             "registered (and any stamp duty paid). Leave at 0 to turn the "
             "reminder off until this is confirmed with your legal team.",
    )
    e_signature_legally_confirmed = fields.Boolean(
        string='E-Signature Legally Confirmed',
        tracking=True,
        default=False,
        help="Whether electronic signatures carry legal validity for "
             "minutes and resolutions under the law that applies to your "
             "company. Leave unchecked until your legal team confirms this "
             "-- while unchecked, only a manually uploaded signed document "
             "can complete signing.",
    )
    minutes_retention_default_years = fields.Integer(
        string='Default Minutes Retention Period (years)',
        tracking=True,
        default=10,
        help="How long signed minutes are kept on file. Defaults to 10 "
             "years; confirm with your legal team whether this matches "
             "your jurisdiction's statutory retention requirement.",
    )
    special_resolution_majority_threshold = fields.Float(
        string='Special Resolution Majority Threshold',
        tracking=True,
        help="The fraction of for-plus-against votes a special resolution "
             "must clear to pass (e.g. 0.75 for a three-quarters majority). "
             "Leave at 0 to keep special resolutions from being tallied "
             "until your company's articles/legal requirement is confirmed.",
    )
    resolution_voting_window_days = fields.Integer(
        string='Resolution Voting Window (days)',
        tracking=True,
        help="How many days a resolution stays open for voting before it "
             "closes and tallies itself automatically. Leave at 0 to keep "
             "voting open until a Secretary tallies it manually.",
    )
    resolution_notice_period_days = fields.Integer(
        string='Resolution Notice Period (days)',
        tracking=True,
        help="Minimum number of days' notice required between opening a "
             "resolution for voting and the date of its meeting. Leave at "
             "0 to turn this check off. Standalone (written) resolutions "
             "have no meeting date and are never affected by this.",
    )
    resolution_meeting_state_gate_enabled = fields.Boolean(
        string='Block Voting Before Meeting Is Scheduled',
        tracking=True,
        default=False,
        help="When enabled, a resolution cannot be opened for voting while "
             "its meeting is still in Draft. Off by default, since meetings "
             "start in Draft and many boards open resolutions before "
             "formally scheduling the meeting.",
    )
    resolution_tie_break_enabled = fields.Boolean(
        string="Allow Chair's Casting Vote on Ties",
        tracking=True,
        default=False,
        help="When enabled, a tied vote waits for a Secretary or Board "
             "Administrator to record a casting-vote decision instead of "
             "automatically failing. Casting-vote authority is currently "
             "limited to those two roles until a dedicated Chair role is "
             "introduced.",
    )
    written_resolution_quorum_percentage = fields.Float(
        string='Written Resolution Quorum (%)',
        tracking=True,
        help="The fraction of eligible voters who must vote on a "
             "standalone (meeting-less) resolution for quorum to be "
             "considered met (e.g. 0.5 for half). Leave at 0 to treat "
             "quorum as always met.",
    )
    meeting_notice_period_days = fields.Integer(
        string='Meeting Notice Period (days)',
        tracking=True,
        help="Minimum number of days' notice required between scheduling "
             "a meeting and its date. Leave at 0 to turn this check off.",
    )
    minutes_require_different_approver = fields.Boolean(
        string='Require a Different Approver for Minutes',
        tracking=True,
        default=False,
        help="When enabled, minutes cannot be approved by the same person "
             "who submitted them for approval. Off by default. Note: this "
             "only prevents self-approval -- it does not yet implement a "
             "full \"the Board approves minutes\" workflow.",
    )
    board_pack_min_lead_days = fields.Integer(
        string='Board Pack Minimum Lead Time (days)',
        tracking=True,
        help="Minimum number of days before the meeting that a board pack "
             "must be distributed by. Leave at 0 to turn this check off.",
    )
    agenda_freeze_on_schedule = fields.Boolean(
        string='Freeze Agenda Once Scheduled',
        tracking=True,
        default=False,
        help="When enabled, agenda items can no longer be added once a "
             "meeting leaves Draft. Off by default: the agenda stays "
             "editable until the meeting is fully Closed.",
    )
    meeting_close_requires_minutes_approved = fields.Boolean(
        string='Require Approved Minutes to Close a Meeting',
        tracking=True,
        default=False,
        help="When enabled, a meeting cannot be closed until its minutes "
             "reach Approved or Signed -- not just submitted For Approval.",
    )

    @api.constrains('minutes_retention_default_years')
    def _check_minutes_retention_positive(self):
        for rec in self:
            if rec.minutes_retention_default_years <= 0:
                raise ValidationError(_(
                    'Default Minutes Retention Period must be at least 1 year.'
                ))

    @api.constrains('special_resolution_majority_threshold', 'written_resolution_quorum_percentage')
    def _check_fraction_fields_in_range(self):
        for rec in self:
            for field_name, label in (
                ('special_resolution_majority_threshold', 'Special Resolution Majority Threshold'),
                ('written_resolution_quorum_percentage', 'Written Resolution Quorum (%)'),
            ):
                value = rec[field_name]
                if value and not (0 < value <= 1):
                    raise ValidationError(_(
                        '%s must be a fraction between 0 and 1 (e.g. 0.75 '
                        'for 75%%), or 0 to leave it unconfigured.'
                    ) % label)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_config_parameters()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field_name in vals for field_name in _CONFIG_PARAMETER_FIELDS):
            self._sync_config_parameters()
        return res

    def _sync_config_parameters(self):
        """Push each field's value into the ir.config_parameter key that the
        owning module's business logic actually reads. Integer fields at 0
        clear the parameter entirely (get_param then returns None, matching
        the existing "unset = disabled" convention those crons already
        implement) rather than persisting a literal "0"."""
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        for rec in self:
            for field_name, (param_key, field_type, clearable) in _CONFIG_PARAMETER_FIELDS.items():
                value = rec[field_name]
                if field_type == 'boolean':
                    IrConfigParameter.set_param(param_key, 'True' if value else 'False')
                elif clearable and not value:
                    IrConfigParameter.set_param(param_key, False)
                else:
                    IrConfigParameter.set_param(param_key, str(value))

    @api.model
    def _get_or_create_for_company(self, company=None):
        """Open (or lazily create) the single config record for a company,
        seeding its fields from any value an admin may have already set
        directly via System Parameters before this UI existed, so switching
        to this page never silently resets a confirmed value back to 0."""
        company = company or self.env.company
        record = self.search([('company_id', '=', company.id)], limit=1)
        if record:
            return record

        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        vals = {'company_id': company.id}
        for field_name, (param_key, field_type, _clearable) in _CONFIG_PARAMETER_FIELDS.items():
            raw = IrConfigParameter.get_param(param_key)
            field = self._fields[field_name]
            default_value = field.default(self) if field.default else 0
            if field_type == 'boolean':
                vals[field_name] = raw in ('True', '1')
            elif field_type == 'float':
                try:
                    vals[field_name] = float(raw) if raw else default_value
                except (TypeError, ValueError):
                    vals[field_name] = default_value
            else:
                try:
                    vals[field_name] = int(raw) if raw else default_value
                except (TypeError, ValueError):
                    vals[field_name] = default_value
        return self.create(vals)

    @api.model
    def action_open_governance_config(self):
        """Window action target: always resolves to the current company's
        record (creating it on first visit), regardless of which record id
        the stale menu action was last pointed at."""
        record = self._get_or_create_for_company()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'govoo.governance.config',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }
