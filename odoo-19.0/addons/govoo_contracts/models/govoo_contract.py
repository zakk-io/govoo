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

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = '/my/contracts/%s' % rec.id

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

    def action_approve(self):
        self._validate_state_transition('approved')
        self._check_board_approval_gate()
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
        self._validate_state_transition('terminated')
        self.write({'state': 'terminated'})
