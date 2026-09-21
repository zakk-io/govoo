# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GovooContractClause(models.Model):
    """Clause library (FR-CM-04): standard vs optional grouping, with a
    mandatory flag. Reusable across templates and snapshotted onto each
    generated contract's clause_ids (docs/spec/modules/govoo_contracts.md).
    """
    _name = 'govoo.contract.clause'
    _description = 'Contract Clause'
    _inherit = ['mail.thread']
    _order = 'is_mandatory desc, name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    body = fields.Html(
        string='Clause Text',
    )
    is_mandatory = fields.Boolean(
        string='Mandatory',
        default=False,
        tracking=True,
        help='Mandatory clauses are always included when generating a '
             'contract from a template that lists this clause; optional '
             'clauses are only included where explicitly selected.',
    )
    clause_category = fields.Selection(
        selection=[
            ('standard', 'Standard'),
            ('optional', 'Optional'),
        ],
        string='Category',
        default='standard',
        tracking=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
