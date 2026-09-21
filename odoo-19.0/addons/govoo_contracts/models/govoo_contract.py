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
        """draft -> in_approval. Board-approval/delegation-of-authority/
        related-party gates are added on top of this action by the
        Approval Routing, Delegation-of-Authority, and Related-Party
        Checks feature clusters (issues #169-171) -- not implemented here.
        """
        self._validate_state_transition('in_approval')
        self.write({'state': 'in_approval'})

    def action_approve(self):
        self._validate_state_transition('approved')
        self.write({'state': 'approved'})

    def action_execute(self):
        self._validate_state_transition('executed')
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
