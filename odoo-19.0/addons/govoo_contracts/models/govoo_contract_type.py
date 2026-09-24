# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GovooContractType(models.Model):
    """Contract type catalogue (FR-CM-02).

    requires_board_approval / approval_threshold / retention_years are
    configuration data, never hard-coded literals -- BR-CM-001 and FR-CM-18
    (docs/spec/decisions/open-decisions.md items 27, 28 remain [CONFIRM];
    this model only provides the configurable mechanism).
    """
    _name = 'govoo.contract.type'
    _description = 'Contract Type'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    requires_board_approval = fields.Boolean(
        string='Requires Board Approval',
        default=False,
        help='BR-CM-001: contracts of this type cannot reach "approved" '
             'without a linked, passed board resolution.',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    approval_threshold = fields.Monetary(
        string='Board-Approval Value Threshold',
        currency_field='currency_id',
        help='A contract of this type with value at or above this threshold '
             'also requires board approval (BR-CM-001), regardless of the '
             'requires_board_approval flag. Configuration data -- never a '
             'hard-coded amount (docs/spec/decisions/open-decisions.md #27).',
    )
    retention_years = fields.Integer(
        string='Retention (Years)',
        help='FR-CM-18: statutory/contractual retention period for this '
             'contract type, read at compute time by govoo.contract -- '
             'never a Python literal, same discipline as govoo_rw retention '
             'config for govoo.minutes.',
    )
    renewal_notice_days = fields.Integer(
        string='Renewal/Expiry Notice (Days)',
        default=0,
        help='FR-CM-11/BR-CM-006: how many days before a contract of this '
             'type reaches its End Date to stage a reminder, via the '
             'existing govoo_compliance-style mail.activity mechanism. '
             '0 (default) disables the reminder for this type.',
    )
    e_signature_enabled = fields.Boolean(
        string='E-Signature Enabled',
        default=False,
        help='Issue #199: a business-level opt-in for e-signature on '
             'contracts of this type, separate from (and in addition to) '
             'the BR-CM-005 legal-confirmation gate. Some organizations are '
             'legally required to use a government procurement portal '
             'instead of in-app e-signing, so even once e-signature is '
             'confirmed legally valid, individual contract types must '
             'still be able to opt out. Defaults to False: e-signature is '
             'off until explicitly enabled for a type, on top of the '
             'legal gate also being satisfied.',
    )
