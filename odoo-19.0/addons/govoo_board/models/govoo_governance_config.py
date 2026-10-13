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
    charge_registration_deadline_days = fields.Integer(
        string='Charge Registration Deadline (days)',
        tracking=True,
        help="[CONFIRM] Statutory window, in days from a charge's creation date, "
             "to register it with the Registrar before it risks being void against "
             "a liquidator/creditors. 0 keeps the reminder disabled until confirmed.",
    )
    beneficial_owner_declaration_deadline_days = fields.Integer(
        string='Beneficial Owner Declaration Deadline (days)',
        tracking=True,
        help="[CONFIRM] Statutory window, in days from becoming registrable, to "
             "declare/file a new beneficial owner. 0 keeps the reminder disabled "
             "until confirmed.",
    )
    certificate_issuance_deadline_days = fields.Integer(
        string='Share Certificate Issuance Deadline (days)',
        tracking=True,
        help="[CONFIRM] Statutory window, in days from allotment, to issue a share "
             "certificate to the shareholder. 0 keeps the reminder disabled until "
             "confirmed.",
    )
    transfer_registration_deadline_days = fields.Integer(
        string='Share Transfer Registration Deadline (days)',
        tracking=True,
        help="[CONFIRM] Statutory window, in days from the transfer date, to "
             "register a share transfer (and pay any stamp duty). 0 keeps the "
             "reminder disabled until confirmed.",
    )
    e_signature_legally_confirmed = fields.Boolean(
        string='E-Signature Legally Confirmed',
        tracking=True,
        default=False,
        help="[CONFIRM] BR-BOARD-008 / open-decisions.md item 3: whether "
             "e-signatures carry legal validity for minutes/resolutions under "
             "the applicable law. Leave unchecked until confirmed -- while "
             "unchecked, e-signing stays closed and only a manually uploaded "
             "signed document can complete signing.",
    )
    minutes_retention_default_years = fields.Integer(
        string='Default Minutes Retention Period (years)',
        tracking=True,
        default=10,
        help="[CONFIRM] open-decisions.md item 13: how long signed minutes are "
             "retained when govoo_rw is not installed or has no active retention "
             "rule for 'minutes'. Defaults to 10 years pending legal confirmation "
             "of the 10-year statutory retention vs. data-subject erasure "
             "reconciliation.",
    )
    special_resolution_majority_threshold = fields.Float(
        string='Special Resolution Majority Threshold',
        tracking=True,
        help="[CONFIRM] BR-BOARD-005 / open-decisions.md item 11: fraction "
             "(e.g. 0.75) of for+against votes a 'special' resolution must "
             "clear. 0 keeps special resolutions blocked from tallying "
             "until confirmed (company articles / Rwandan law).",
    )
    resolution_voting_window_days = fields.Integer(
        string='Resolution Voting Window (days)',
        tracking=True,
        help='Issue #269: days after a resolution opens for voting before '
             'it auto-closes (tallies) via a daily cron. 0 keeps voting '
             'open until a Secretary manually tallies it -- the original '
             'behavior.',
    )
    resolution_notice_period_days = fields.Integer(
        string='Resolution Notice Period (days)',
        tracking=True,
        help='Issue #269: minimum days between opening a resolution for '
             "voting and its linked meeting's date. 0 disables the check. "
             'Standalone (written) resolutions have no meeting date and are '
             'never gated by this.',
    )
    resolution_meeting_state_gate_enabled = fields.Boolean(
        string='Block Voting Before Meeting Is Scheduled',
        tracking=True,
        default=False,
        help='Issue #269: when enabled, a resolution cannot open for '
             "voting while its meeting is still in Draft state. Off by "
             'default: govoo.meeting defaults to Draft, so this is an '
             'opt-in governance policy, not a correction of a bug.',
    )
    resolution_tie_break_enabled = fields.Boolean(
        string="Allow Chair's Casting Vote on Ties",
        tracking=True,
        default=False,
        help='Issue #269: when enabled, a tied simple-majority vote waits '
             'for a Secretary/Board Administrator casting-vote decision '
             'instead of automatically failing. [CONFIRM]: casting-vote '
             'authority is restricted to those two groups until a '
             'dedicated chair role is confirmed.',
    )
    written_resolution_quorum_percentage = fields.Float(
        string='Written Resolution Quorum (%)',
        tracking=True,
        help='[CONFIRM] Issue #269: fraction (e.g. 0.5) of eligible voters '
             'who must vote on a standalone (meeting-less) resolution for '
             'quorum to be met. 0 keeps the original always-met behavior.',
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
