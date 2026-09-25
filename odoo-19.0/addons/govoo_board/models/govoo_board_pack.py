# Part of Govoo. See LICENSE file for full copyright and licensing details.

import base64
import io

from odoo import _, api, fields, models
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
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
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

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.meeting_id and not rec.meeting_id.pack_id:
                rec.meeting_id.pack_id = rec.id
        return records

    def action_compile(self):
        """Compile agenda + linked documents into a distributable pack.

        Per-recipient redaction: confidential items are excluded for
        unauthorized recipients BEFORE generating their copy (BR-BOARD-003).
        Generates the merged master PDF (agenda + linked documents) and
        attaches it as document_id; redaction of confidential items for
        a given recipient's copy is applied at render time (portal view,
        recipient.redacted_item_ids), not by producing a separate PDF
        per recipient. Feature-flagged: degrades to ir.attachment on
        Community.
        """
        for rec in self:
            agenda_items = rec.meeting_id.agenda_ids.sorted('sequence')
            # Create distribution records for each attendee
            existing_partners = rec.distribution_ids.mapped('partner_id')
            new_partners = rec.meeting_id.attendee_ids.filtered(
                lambda p: p not in existing_partners,
            )
            for partner in new_partners:
                # Per-recipient authorization (BR-BOARD-003): each
                # recipient's redacted set depends on THEIR OWN
                # authorization for each confidential item, not a
                # single blanket list applied to everyone.
                redacted = agenda_items.filtered(
                    lambda item, p=partner: not item._is_authorized_for(p),
                )
                self.env['govoo.board.pack.recipient'].create({
                    'pack_id': rec.id,
                    'partner_id': partner.id,
                    'redacted_item_ids': [(6, 0, redacted.ids)],
                })
            rec._generate_document()
            rec.state = 'compiled'

    def _generate_document(self):
        """Generate the merged master board pack PDF and attach it.

        This is the Secretary's own internal reference/print copy: every
        agenda item is included regardless of confidentiality, same as
        before. Per-recipient redacted copies are generated separately
        by _generate_recipient_document(), never from this attachment.
        """
        self.ensure_one()
        report = self.env.ref('govoo_board.action_report_board_pack')
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report.id, self.ids,
        )
        pdf_content = self._merge_agenda_documents(
            pdf_content, self.meeting_id.agenda_ids,
        )
        # _render_qweb_pdf returns raw PDF bytes, but ir.attachment.datas
        # is a Binary field that expects base64 -- writing the raw bytes
        # directly silently base64-decodes them into garbage, producing
        # an attachment that looks fine (right mimetype/name) but isn't
        # a valid PDF at all.
        attachment = self.env['ir.attachment'].create({
            'name': 'Board Pack - %s.pdf' % (self.meeting_id.name,),
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        self.document_id = attachment

    def _generate_recipient_document(self, recipient):
        """Generate THIS recipient's own copy of the board pack, on demand.

        Unlike _generate_document()'s stored master copy, a confidential
        agenda item this recipient isn't authorized for is fully omitted
        here -- title and description, not just a hidden badge -- and
        only the PDF attachments of items they CAN see get merged in.
        Generated fresh on every download rather than cached, so it
        always reflects the recipient's current authorization.
        """
        self.ensure_one()
        report = self.env.ref('govoo_board.action_report_board_pack')
        redacted_ids = recipient.redacted_item_ids.ids
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report.id, self.ids,
            data={'redacted_item_ids': redacted_ids},
        )
        visible_items = self.meeting_id.agenda_ids.filtered(
            lambda item: item.id not in redacted_ids,
        )
        return self._merge_agenda_documents(pdf_content, visible_items)

    def _merge_agenda_documents(self, pdf_content, visible_items):
        """Merge each visible agenda item's PDF attachments (e.g. the
        previous meeting's signed minutes, attached to an "Approval of
        Minutes" item) as real pages after the agenda body, in agenda
        order. Non-PDF attachments (Word docs, images, etc.) are left
        out of the merge -- they're still listed by name in the agenda
        body -- rather than failing the whole pack over one file Odoo
        can't merge as PDF pages.
        """
        self.ensure_one()
        streams = [io.BytesIO(pdf_content)]
        for item in visible_items.sorted('sequence'):
            for doc in item.document_ids:
                if (doc.mimetype or '').split(';')[0] != 'application/pdf':
                    continue
                try:
                    streams.append(io.BytesIO(base64.b64decode(doc.datas)))
                except Exception:
                    continue
        if len(streams) == 1:
            return pdf_content

        def _skip_unmergeable(error, error_stream):
            streams.remove(error_stream)

        with self.env['ir.actions.report']._merge_pdfs(
            streams, handle_error=_skip_unmergeable,
        ) as merged:
            return merged.getvalue()

    def action_distribute(self):
        """Distribute compiled pack to recipients via both an in-app
        portal notification and an actual email (issue #203) -- the two
        channels are sent together for the same distribution event, one
        does not replace the other. Recipients with no registered email
        block the whole distribution with a clear, actionable error
        rather than silently skipping them (a named pain point in the
        original request)."""
        template = self.env.ref(
            'govoo_board.mail_template_board_pack_distribution',
            raise_if_not_found=False,
        )
        for rec in self:
            if rec.state != 'compiled':
                raise ValidationError(_('Pack must be compiled before distribution.'))
            pending = rec.distribution_ids.filtered(lambda d: not d.sent_date)
            missing_email = pending.filtered(lambda d: not d.partner_id.email)
            if missing_email:
                raise ValidationError(_(
                    'Cannot distribute: the following recipients have no '
                    'registered email address: %s'
                ) % ', '.join(missing_email.mapped('partner_id.name')))
            for dist in pending:
                dist.sent_date = fields.Datetime.now()
                # In-app portal notification
                rec.message_post(
                    body='Board pack is available for your review.',
                    partner_ids=dist.partner_id.ids,
                    subtype_xmlid='mail.mt_comment',
                )
                # Actual email, linking to this recipient's own
                # correctly-redacted portal copy rather than attaching
                # the unredacted master document_id (see template
                # comment for why).
                if template:
                    template.send_mail(dist.id, force_send=True)
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
