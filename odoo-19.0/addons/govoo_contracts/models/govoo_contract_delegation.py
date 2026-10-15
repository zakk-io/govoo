# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class GovooContractDelegation(models.Model):
    """Delegation-of-authority matrix (FR-CM-08, BR-CM-002): who may
    execute a contract up to what value, optionally scoped to a specific
    contract type. Configuration data -- the matrix itself is [CONFIRM]
    (docs/spec/decisions/open-decisions.md item 28); this model only
    provides the configurable mechanism, never a hard-coded limit.
    """
    _name = 'govoo.contract.delegation'
    _description = 'Contract Delegation of Authority'
    _order = 'user_id, contract_type_id'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver',
        required=True,
        ondelete='cascade',
    )
    contract_type_id = fields.Many2one(
        comodel_name='govoo.contract.type',
        string='Contract Type',
        ondelete='cascade',
        help='Leave empty for a limit that applies to every contract type.',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    max_value = fields.Monetary(
        string='Maximum Contract Value',
        currency_field='currency_id',
        required=True,
        help='The highest contract value this user may execute, for the '
             'given contract type (or any type, if left empty).',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    @api.depends('user_id.name', 'contract_type_id.name')
    def _compute_display_name(self):
        # No plain-text field on this model, so display_name would
        # otherwise fall back to the raw "govoo.contract.delegation,<id>" string.
        for rec in self:
            if rec.user_id:
                rec.display_name = '%s — %s' % (
                    rec.user_id.name, rec.contract_type_id.name or _('All Contract Types'),
                )
            else:
                rec.display_name = _('Contract Delegation')
