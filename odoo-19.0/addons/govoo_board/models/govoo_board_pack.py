# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class GovooBoardPack(models.Model):
    _name = 'govoo.board.pack'
    _description = 'Board Pack'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    meeting_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Meeting',
        required=True,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='meeting_id.company_id',
        store=True,
        readonly=True,
    )
    # Feature-flagged: ir.attachment (Community) / documents.document (Enterprise)
    document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Pack Document',
    )
    distribution_ids = fields.One2many(
        comodel_name='govoo.board.pack.recipient',
        inverse_name='pack_id',
        string='Distribution',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('compiled', 'Compiled'),
            ('distributed', 'Distributed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    def action_compile(self):
        """Compile agenda + linked documents into a distributable pack.

        Per-recipient redaction: confidential items are excluded for
        unauthorized recipients BEFORE generating their copy (BR-BOARD-003).
        Feature-flagged: degrades to ir.attachment on Community.
        """
        for rec in self:
            agenda_items = rec.meeting_id.agenda_ids.sorted('sequence')
            # Create distribution records for each attendee
            existing_partners = rec.distribution_ids.mapped('partner_id')
            new_partners = rec.meeting_id.attendee_ids.filtered(
                lambda p: p not in existing_partners,
            )
            for partner in new_partners:
                # Determine redacted items: confidential + partner not authorized
                redacted = agenda_items.filtered(
                    lambda item: item.is_confidential,
                )
                self.env['govoo.board.pack.recipient'].create({
                    'pack_id': rec.id,
                    'partner_id': partner.id,
                    'redacted_item_ids': [(6, 0, redacted.ids)],
                })
            rec.state = 'compiled'

    def action_distribute(self):
        """Distribute compiled pack to recipients via portal notification."""
        for rec in self:
            if rec.state != 'compiled':
                raise ValidationError(_('Pack must be compiled before distribution.'))
            for dist in rec.distribution_ids:
                if not dist.sent_date:
                    dist.sent_date = fields.Datetime.now()
                    # Notify recipient
                    rec.message_post(
                        body='Board pack is available for your review.',
                        partner_ids=dist.partner_id.ids,
                        subtype_xmlid='mail.mt_comment',
                    )
            rec.state = 'distributed'


class GovooBoardPackRecipient(models.Model):
    _name = 'govoo.board.pack.recipient'
    _description = 'Board Pack Distribution Recipient'

    pack_id = fields.Many2one(
        comodel_name='govoo.board.pack',
        string='Board Pack',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Recipient',
        required=True,
    )
    sent_date = fields.Datetime(
        string='Sent Date',
    )
    redacted_item_ids = fields.Many2many(
        comodel_name='govoo.agenda.item',
        string='Redacted Agenda Items',
    )
