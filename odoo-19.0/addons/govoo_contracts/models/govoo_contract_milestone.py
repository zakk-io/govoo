# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GovooContractMilestone(models.Model):
    """Deliverable/payment milestone tracking (addendum section 3.3)."""
    _name = 'govoo.contract.milestone'
    _description = 'Contract Milestone'
    _inherit = ['mail.thread']
    _order = 'date asc'

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
    date = fields.Date(
        string='Date',
        tracking=True,
    )
    value = fields.Monetary(
        string='Value',
        currency_field='currency_id',
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('delivered', 'Delivered'),
            ('paid', 'Paid'),
        ],
        string='Status',
        default='pending',
        required=True,
        tracking=True,
    )
