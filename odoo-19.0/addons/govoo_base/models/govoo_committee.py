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
        domain=[('role', '!=', 'secretary'), ('state', '=', 'active')],
        help='Anyone with an active, committee-scoped governance role '
             '(member, chair, MD, director) — excludes the administrative '
             'Secretary role and resigned appointments. Portal record rules '
             'key off this field, so a portal-only Chair must be included '
             "here to see their own committee's meetings/minutes/"
             'resolutions, and a resigned appointee must drop out of it.',
    )
    member_count = fields.Integer(
        string='Members',
        compute='_compute_member_count',
    )
    meeting_count = fields.Integer(
        string='Meetings',
        compute='_compute_meeting_count',
    )

    @api.depends('member_ids')
    def _compute_member_count(self):
        for rec in self:
            rec.member_count = len(rec.member_ids)

    def _compute_meeting_count(self):
        Meeting = self.env['govoo.meeting']
        for rec in self:
            rec.meeting_count = Meeting.search_count([('committee_id', '=', rec.id)])

    def action_view_members(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Members',
            'res_model': 'govoo.appointment',
            'view_mode': 'list,form',
            'domain': [
                ('committee_id', '=', self.id),
                ('role', '!=', 'secretary'),
                ('state', '=', 'active'),
            ],
            'context': {'default_committee_id': self.id},
        }

    def action_view_meetings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Meetings',
            'res_model': 'govoo.meeting',
            'view_mode': 'list,form,kanban',
            'domain': [('committee_id', '=', self.id)],
            'context': {'default_committee_id': self.id},
        }
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
