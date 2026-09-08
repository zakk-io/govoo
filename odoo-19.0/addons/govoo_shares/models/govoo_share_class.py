# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooShareClass(models.Model):
    _name = 'govoo.share.class'
    _description = 'Share Class'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(
        string='Share Class Name',
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
    nominal_value = fields.Monetary(
        string='Nominal Value',
        currency_field='currency_id',
        tracking=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    votes_per_share = fields.Float(
        string='Votes per Share',
        default=1.0,
        tracking=True,
    )
    total_authorised = fields.Integer(
        string='Total Authorised Shares',
        required=True,
        tracking=True,
    )
    is_redeemable = fields.Boolean(
        string='Redeemable',
        default=False,
        tracking=True,
    )
    allotment_ids = fields.One2many(
        comodel_name='govoo.share.allotment',
        inverse_name='share_class_id',
        string='Allotments',
    )
    holding_ids = fields.One2many(
        comodel_name='govoo.share.holding',
        inverse_name='share_class_id',
        string='Holdings',
    )
    transfer_ids = fields.One2many(
        comodel_name='govoo.share.transfer',
        inverse_name='share_class_id',
        string='Transfers',
    )
    total_allotted = fields.Integer(
        string='Total Allotted',
        compute='_compute_total_allotted',
        store=True,
    )

    @api.depends('allotment_ids.quantity')
    def _compute_total_allotted(self):
        for rec in self:
            rec.total_allotted = sum(rec.allotment_ids.mapped('quantity'))

    @api.constrains('total_authorised')
    def _check_total_authorised(self):
        for rec in self:
            if rec.total_authorised <= 0:
                raise ValidationError(
                    _('Total Authorised Shares must be greater than zero.')
                )

    @api.constrains('nominal_value')
    def _check_nominal_value(self):
        for rec in self:
            if rec.nominal_value < 0:
                raise ValidationError(_('Nominal Value cannot be negative.'))
