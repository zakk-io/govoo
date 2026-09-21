# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# done/waived are terminal -- mirrors govoo.compliance.instance.state's
# filed/waived pattern (data-model/state-machines.md), not a new
# vocabulary.
_TERMINAL_STATES = ('done', 'waived')


class GovooContractObligation(models.Model):
    """Obligation tracking (FR-CM-13): due_date feeds the existing
    govoo_compliance reminder engine (BR-CM-006, issue #173's
    govoo.contract.cron) -- this model owns no cron/reminder logic of
    its own.
    """
    _name = 'govoo.contract.obligation'
    _description = 'Contract Obligation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date asc'

    contract_id = fields.Many2one(
        comodel_name='govoo.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='contract_id.company_id',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='contract_id.currency_id',
        readonly=True,
    )
    name = fields.Char(
        string='Description',
        required=True,
        tracking=True,
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True,
    )
    responsible_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        tracking=True,
    )
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
    )
    lead_time_days = fields.Integer(
        string='Reminder Lead Time (Days)',
        default=7,
        help='How many days before due_date to stage a reminder via the '
             'existing govoo_compliance-style mail.activity mechanism '
             '(BR-CM-006), same pattern as '
             'govoo.compliance.obligation.lead_time_days.',
    )
    state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('done', 'Done'),
            ('overdue', 'Overdue'),
            ('waived', 'Waived'),
        ],
        string='Status',
        default='open',
        required=True,
        tracking=True,
    )

    def write(self, vals):
        """Block transitions out of terminal states, same discipline as
        govoo.compliance.instance."""
        if 'state' in vals:
            for rec in self:
                if rec.state in _TERMINAL_STATES:
                    raise ValidationError(_(
                        'Cannot change status from "%s" to "%s". '
                        'Done and Waived are terminal states.'
                    ) % (rec.state, vals['state']))
        return super().write(vals)

    def action_done(self):
        for rec in self:
            if rec.state not in ('open', 'overdue'):
                raise ValidationError(_('Only Open or Overdue obligations can be marked Done.'))
        self.write({'state': 'done'})

    def action_waive(self):
        for rec in self:
            if rec.state in _TERMINAL_STATES:
                raise ValidationError(_('This obligation is already in a terminal state.'))
        self.write({'state': 'waived'})

    @api.model
    def _cron_escalate_overdue(self):
        """Daily: transition overdue obligations to 'overdue' -- same
        mechanism as govoo_compliance.cron._cron_escalate_late, called
        from govoo.contract.cron (issue #173) rather than a second cron
        engine."""
        today = fields.Date.context_today(self)
        obligations = self.search([
            ('state', '=', 'open'),
            ('due_date', '<', today),
        ])
        obligations.write({'state': 'overdue'})
