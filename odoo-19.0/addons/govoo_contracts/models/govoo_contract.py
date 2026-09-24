# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# States in which the executed document is locked (BR-CM-004) and the
# record itself can no longer be deleted -- everything from 'executed'
# onward per docs/spec/data-model/state-machines.md govoo.contract.state.
_LOCKED_STATES = ('executed', 'active', 'expired', 'terminated')

# Strictly forward, one step at a time -- same discipline as
# govoo.meeting.state (BR-BOARD-002), applied here as an
# engineering-consistency choice (docs/spec/data-model/state-machines.md).
_ALLOWED_TRANSITIONS = {
    'draft': ['in_approval'],
    'in_approval': ['approved'],
    'approved': ['executed'],
    'executed': ['active'],
    'active': ['expired', 'terminated'],
}


class GovooContract(models.Model):
    _name = 'govoo.contract'
    _description = 'Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Contract Reference',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    contract_type_id = fields.Many2one(
        comodel_name='govoo.contract.type',
        string='Contract Type',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    counterparty_id = fields.Many2one(
        comodel_name='res.partner',
        string='Counterparty',
        required=True,
        tracking=True,
    )
    template_id = fields.Many2one(
        comodel_name='govoo.contract.template',
        string='Generated From Template',
        ondelete='set null',
        help='Informational only -- clause_ids is a snapshot at '
             'generation time, so later edits to the template never '
             'retroactively change an already-generated contract.',
    )
    clause_ids = fields.Many2many(
        comodel_name='govoo.contract.clause',
        string='Clauses',
    )
    obligation_ids = fields.One2many(
        comodel_name='govoo.contract.obligation',
        inverse_name='contract_id',
        string='Obligations',
    )
    milestone_ids = fields.One2many(
        comodel_name='govoo.contract.milestone',
        inverse_name='contract_id',
        string='Milestones',
    )
    obligation_count = fields.Integer(
        string='Obligations',
        compute='_compute_obligation_count',
    )
    milestone_count = fields.Integer(
        string='Milestones',
        compute='_compute_milestone_count',
    )
    is_related_party = fields.Boolean(
        string='Related Party',
        compute='_compute_is_related_party',
        store=True,
        help='BR-CM-003: True when the counterparty is a director, '
             'shareholder, officer, or beneficial owner of this company '
             '-- read from the existing govoo_base/govoo_secretarial '
             'classification, never a second, independent classification.',
    )
    conflict_declared = fields.Boolean(
        string='Conflict of Interest Declared',
        tracking=True,
        help='Required before a related-party contract can be approved '
             '(BR-CM-003) -- mirrors govoo.vote.is_conflicted\'s '
             'declared-interest pattern (BR-BOARD-007).',
    )
    conflict_declaration_notes = fields.Text(
        string='Conflict Declaration Notes',
    )
    portal_approver_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Named Approvers (Portal)',
        help='Partners other than the counterparty who should see this '
             'contract in the Contract Viewer Portal as a named approver '
             '(BR-CM-007, security/record-rules.md section 6b) -- resolves '
             'the previously-open "named approver" data-model gap '
             'explicitly, rather than assuming it always equals '
             'counterparty_id.',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    value = fields.Monetary(
        string='Contract Value',
        currency_field='currency_id',
        tracking=True,
    )
    date_start = fields.Date(
        string='Start Date',
        tracking=True,
    )
    date_end = fields.Date(
        string='End Date',
        tracking=True,
    )
    renewal_type = fields.Selection(
        selection=[
            ('fixed', 'Fixed Term'),
            ('auto', 'Evergreen (Auto-Renew)'),
        ],
        string='Renewal Type',
        default='fixed',
        required=True,
        tracking=True,
    )
    retention_until = fields.Date(
        string='Retention Until',
        compute='_compute_retention_until',
        store=True,
        help='FR-CM-18: computed from contract_type_id.retention_years at '
             'compute time, same discipline as govoo.minutes.'
             'retention_until reading govoo_rw config -- never a Python '
             'literal. Unlike minutes, no statutory default is assumed '
             'here if retention_years is unset: contract retention has '
             'no established default in this project (unlike minutes\' '
             'confirmed 10-year rule, BR-BOARD-004), so an unconfigured '
             'type simply computes no retention date rather than '
             'guessing one.',
    )
    termination_reason = fields.Text(
        string='Termination Reason',
        help='Required before action_terminate() can be called (FR-CM-14) '
             '-- same "field must already be set, the action only '
             'transitions" pattern as govoo.compliance.instance.action_file '
             'requiring reference_no/filed_date.',
    )
    executed_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Executed Document',
        tracking=True,
        help='Write-once once the contract reaches "executed" (BR-CM-004): '
             'an amendment or renewal must attach a new document, never '
             'edit this one in place.',
    )
    resolution_id = fields.Many2one(
        comodel_name='govoo.resolution',
        string='Board Resolution',
        tracking=True,
        help='Required, and must be in state "passed", before this '
             'contract can be approved when its type requires board '
             'approval or its value meets the type\'s approval threshold '
             '(BR-CM-001).',
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a signing document is generated for this field, check
    # self.env['govoo.feature.flags'].is_sign_app_installed() to use
    # sign.request instead, falling back to ir.attachment on Community --
    # same pattern as govoo_board's govoo.resolution.sign_request_id.
    sign_request_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Sign Request',
        tracking=True,
    )
    sign_status = fields.Selection(
        selection=[
            ('not_sent', 'Not Sent'),
            ('sent', 'Sent for Signature'),
            ('signed', 'Signed'),
            ('declined', 'Declined'),
            ('cancelled', 'Cancelled'),
        ],
        string='E-Signature Status',
        default='not_sent',
        required=True,
        tracking=True,
        help='Issue #199: tracks the e-signature lifecycle for the '
             'document attached to Sign Request. Independent of the main '
             'contract Status -- a contract can be sent for signature at '
             'any point once Sign Request is set.',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_approval', 'In Approval'),
            ('approved', 'Approved'),
            ('executed', 'Executed'),
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('terminated', 'Terminated'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    @api.depends('obligation_ids')
    def _compute_obligation_count(self):
        for rec in self:
            rec.obligation_count = len(rec.obligation_ids)

    @api.depends('milestone_ids')
    def _compute_milestone_count(self):
        for rec in self:
            rec.milestone_count = len(rec.milestone_ids)

    @api.depends('create_date', 'contract_type_id.retention_years')
    def _compute_retention_until(self):
        for rec in self:
            retention_years = rec.contract_type_id.retention_years
            if not rec.create_date or not retention_years:
                rec.retention_until = False
                continue
            rec.retention_until = rec.create_date.replace(
                year=rec.create_date.year + retention_years,
            )

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = '/my/contracts/%s' % rec.id

    @api.depends(
        'counterparty_id.govoo_is_director',
        'counterparty_id.govoo_is_shareholder',
        'counterparty_id.govoo_is_officer',
        'counterparty_id.govoo_is_beneficial_owner',
    )
    def _compute_is_related_party(self):
        for rec in self:
            partner = rec.counterparty_id
            rec.is_related_party = bool(partner) and any((
                partner.govoo_is_director,
                partner.govoo_is_shareholder,
                partner.govoo_is_officer,
                partner.govoo_is_beneficial_owner,
            ))

    @api.constrains('sign_request_id')
    def _check_esignature_legally_confirmed(self):
        """BR-CM-005: contract e-signature reuses the exact same
        Rwandan legal-validity confirmation as govoo_board's
        BR-BOARD-008 -- the same ir.config_parameter key, not a separate
        govoo_contracts-specific flag (docs/spec/decisions/
        open-decisions.md item 26 is one confirmation, not two)."""
        confirmed = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.e_signature_legally_confirmed', 'False',
        ) in ('True', '1')
        if confirmed:
            return
        for rec in self:
            if rec.sign_request_id:
                raise ValidationError(_(
                    'E-signature is not yet confirmed as legally valid '
                    'under Rwandan law (BR-CM-005); Sign Request cannot '
                    'be used. Attach the manually signed copy as the '
                    'Executed Document instead.'
                ))

    def _check_esignature_enabled_for_type(self):
        """Issue #199: business-level opt-in, separate from and in
        addition to the BR-CM-005 legal-confirmation gate above. A
        contract type with e_signature_enabled=False never offers
        e-signature, even once e-signature is legally confirmed -- this
        exists because some organizations are legally required to use a
        government procurement portal instead of in-app e-signing."""
        for rec in self:
            if not rec.contract_type_id.e_signature_enabled:
                raise ValidationError(_(
                    'E-signature is not enabled for contract type "%s". '
                    'Enable it on the contract type, or attach the '
                    'manually signed copy as the Executed Document instead.'
                ) % rec.contract_type_id.name)

    def _check_sign_status_transition(self, target_status):
        allowed = {
            'not_sent': ['sent'],
            'sent': ['signed', 'declined', 'cancelled'],
            'declined': ['sent'],
            'cancelled': ['sent'],
        }
        for rec in self:
            if target_status not in allowed.get(rec.sign_status, []):
                raise ValidationError(_(
                    'Cannot change E-Signature Status from "%s" to "%s".'
                ) % (rec.sign_status, target_status))

    def action_send_for_signature(self):
        """Issue #199: send the Sign Request document for e-signature.
        Gated on both BR-CM-005 (legal confirmation, enforced above at
        the field level the moment Sign Request was set) and the
        e_signature_enabled business toggle checked here explicitly, so
        the error message is specific to this action rather than a
        generic constraint failure."""
        self._check_esignature_enabled_for_type()
        self._check_sign_status_transition('sent')
        for rec in self:
            if not rec.sign_request_id:
                raise ValidationError(_(
                    'Attach a document to Sign Request before sending it '
                    'for signature.'
                ))
            if self.env['govoo.feature.flags'].is_sign_app_installed():
                # [FOLLOW-UP] Native Sign-app integration (creating a real
                # sign.request record via the Sign app's API) is not yet
                # wired up -- untestable in this Community-only dev
                # environment (docs/spec/decisions/open-decisions.md item
                # 3/26 territory: no guessing at an unverified API
                # surface). Falls through to the same manual-tracking
                # status below, which works identically on Community.
                rec.message_post(body=_(
                    'The Sign app is installed, but native e-signature '
                    'request creation is not yet implemented; tracking '
                    'this send manually via E-Signature Status.'
                ))
            rec.sign_status = 'sent'

    def action_mark_signed(self):
        self._check_sign_status_transition('signed')
        self.sign_status = 'signed'

    def action_mark_declined(self):
        self._check_sign_status_transition('declined')
        self.sign_status = 'declined'

    def action_cancel_signature(self):
        self._check_sign_status_transition('cancelled')
        self.sign_status = 'cancelled'

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(_('End Date cannot be earlier than Start Date.'))

    def _validate_state_transition(self, target_state):
        for rec in self:
            if target_state not in _ALLOWED_TRANSITIONS.get(rec.state, []):
                raise ValidationError(
                    _('Cannot transition from "%s" to "%s". '
                      'State transitions must be strictly forward, one step at a time.')
                    % (rec.state, target_state),
                )

    def write(self, vals):
        if 'executed_document_id' in vals:
            for rec in self:
                if rec.state in _LOCKED_STATES and rec.executed_document_id:
                    raise UserError(_(
                        'The executed document is locked once a contract '
                        'reaches "Executed" (BR-CM-004). Attach a new '
                        'document for an amendment or renewal instead of '
                        'editing this one.'
                    ))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in _LOCKED_STATES:
                raise UserError(_(
                    'An executed contract cannot be deleted (BR-CM-004).'
                ))
        return super().unlink()

    def action_view_obligations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Obligations'),
            'res_model': 'govoo.contract.obligation',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }

    def action_view_milestones(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Milestones'),
            'res_model': 'govoo.contract.milestone',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }

    def action_submit(self):
        """draft -> in_approval. Delegation-of-authority and related-party
        gates are added on top of this action by their own feature
        clusters (issues #170-171) -- not implemented here.
        """
        self._validate_state_transition('in_approval')
        self.write({'state': 'in_approval'})

    def _requires_board_approval(self):
        """BR-CM-001: a contract type flagged requires_board_approval, or
        whose configured approval_threshold is met/exceeded by this
        contract's value, needs a passed board resolution before it can
        be approved. Both thresholds are configuration data on
        govoo.contract.type, never a hard-coded value here
        (docs/spec/decisions/open-decisions.md item 27)."""
        self.ensure_one()
        contract_type = self.contract_type_id
        if contract_type.requires_board_approval:
            return True
        if contract_type.approval_threshold and self.value >= contract_type.approval_threshold:
            return True
        return False

    def _check_board_approval_gate(self):
        """BR-CM-001: block in_approval -> approved without a linked,
        passed board resolution when board approval is required."""
        for rec in self:
            if not rec._requires_board_approval():
                continue
            if not rec.resolution_id or rec.resolution_id.state != 'passed':
                raise ValidationError(_(
                    'This contract requires board approval (BR-CM-001): '
                    'link a board resolution in "Passed" state before '
                    'approving it.'
                ))

    def _check_related_party_gate(self):
        """BR-CM-003: a related-party contract cannot be approved until a
        conflict-of-interest declaration is recorded -- mirrors
        govoo.vote.is_conflicted's declared-interest exclusion
        (BR-BOARD-007), applied here as an approval gate rather than a
        tally exclusion."""
        for rec in self:
            if rec.is_related_party and not rec.conflict_declared:
                raise ValidationError(_(
                    'This contract\'s counterparty is a related party '
                    '(BR-CM-003): record a conflict-of-interest '
                    'declaration before approving it.'
                ))

    def action_approve(self):
        self._validate_state_transition('approved')
        self._check_board_approval_gate()
        self._check_related_party_gate()
        self.write({'state': 'approved'})

    def _check_delegation_of_authority(self):
        """BR-CM-002: execution (approved -> executed) is blocked unless
        the executing user's delegated authority, per
        govoo.contract.delegation, covers this contract's type and value.
        Checked for every execution, not only board-approved contracts --
        board approval and delegated signing authority are independent
        controls. The matrix itself is [CONFIRM]-configurable data
        (docs/spec/decisions/open-decisions.md item 28), never a
        hard-coded limit here."""
        delegation_model = self.env['govoo.contract.delegation']
        for rec in self:
            matching = delegation_model.search([
                ('company_id', '=', rec.company_id.id),
                ('user_id', '=', self.env.uid),
                ('contract_type_id', 'in', (rec.contract_type_id.id, False)),
                ('max_value', '>=', rec.value),
            ], limit=1)
            if not matching:
                raise ValidationError(_(
                    'You are not authorized to execute this contract '
                    '(BR-CM-002): no delegation-of-authority entry covers '
                    'your user for this contract type and value.'
                ))

    def action_execute(self):
        self._validate_state_transition('executed')
        self._check_delegation_of_authority()
        self.write({'state': 'executed'})

    def action_activate(self):
        self._validate_state_transition('active')
        self.write({'state': 'active'})

    def action_expire(self):
        self._validate_state_transition('expired')
        self.write({'state': 'expired'})

    def action_terminate(self):
        """active -> terminated. Requires termination_reason to already
        be set (FR-CM-14) -- recorded via mail.thread tracking, not a
        separate audit model."""
        self._validate_state_transition('terminated')
        for rec in self:
            if not rec.termination_reason:
                raise ValidationError(_(
                    'Record a Termination Reason before terminating this '
                    'contract.'
                ))
        self.write({'state': 'terminated'})
