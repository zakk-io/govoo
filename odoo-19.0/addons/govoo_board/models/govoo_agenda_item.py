# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GovooAgendaItem(models.Model):
    _name = 'govoo.agenda.item'
    _description = 'Meeting Agenda Item'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    meeting_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Meeting',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    title = fields.Char(
        string='Title',
        required=True,
    )
    description = fields.Html(
        string='Description',
    )
    presenter_id = fields.Many2one(
        comodel_name='res.partner',
        string='Presenter',
    )
    item_type = fields.Selection(
        selection=[
            ('discussion', 'Discussion'),
            ('decision', 'Decision'),
            ('noting', 'Noting'),
        ],
        string='Type',
        required=True,
    )
    is_confidential = fields.Boolean(
        string='Confidential',
        default=False,
        help='Confidential items are redacted from board packs for unauthorized recipients.',
    )
    # Feature-flagged: ir.attachment (Community) / documents.document (Enterprise)
    document_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Attached Documents',
    )
    resolution_ids = fields.One2many(
        comodel_name='govoo.resolution',
        inverse_name='agenda_item_id',
        string='Resolutions',
    )

    @api.constrains('meeting_id')
    def _check_meeting_not_closed(self):
        msg = 'Cannot add agenda items to a closed meeting.'
        for rec in self:
            if rec.meeting_id and rec.meeting_id.state == 'closed':
                raise ValidationError(msg)
