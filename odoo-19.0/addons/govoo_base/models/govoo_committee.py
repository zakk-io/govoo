# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooCommittee(models.Model):
    _name = 'govoo.committee'
    _description = 'Committee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Committee Name',
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
    parent_committee_id = fields.Many2one(
        comodel_name='govoo.committee',
        string='Parent Committee',
        tracking=True,
        ondelete='set null',
    )
    chair_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Chairperson',
        tracking=True,
    )
    member_ids = fields.One2many(
        comodel_name='govoo.appointment',
        inverse_name='committee_id',
        string='Members',
        domain=[('role', '=', 'committee_member')],
    )
    # Feature-flagged: ir.attachment (Community) / documents.document (Enterprise)
    terms_of_reference_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Terms of Reference',
    )

    @api.constrains('parent_committee_id', 'company_id')
    def _check_parent_committee(self):
        for rec in self:
            if rec.parent_committee_id:
                if rec.parent_committee_id.id == rec.id:
                    raise ValidationError(
                        _('A committee cannot be its own parent.')
                    )
                if rec.parent_committee_id.company_id != rec.company_id:
                    raise ValidationError(
                        _('Parent committee must belong to the same company.')
                    )
                # Cycle check: walk up the parent chain
                visited = set()
                current = rec.parent_committee_id
                while current:
                    if current.id in visited:
                        raise ValidationError(
                            _('A cycle was detected in the committee hierarchy.')
                        )
                    visited.add(current.id)
                    current = current.parent_committee_id
