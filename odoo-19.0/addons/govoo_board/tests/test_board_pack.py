# Part of Govoo. See LICENSE file for full copyright and licensing details.

import base64
import io

from odoo.tests import tagged
from odoo.tools.pdf import PdfFileReader, PdfFileWriter

from .common import GovooBoardTestBase


def _make_blank_pdf(num_pages=1):
    """Build a minimal, real, valid PDF with no dependency on
    wkhtmltopdf -- used as a stand-in for a "previous meeting's signed
    minutes" attachment or a QWeb-rendered pack body in tests."""
    writer = PdfFileWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@tagged('post_install', '-at_install', 'govoo_board')
class GovooBoardPackTC(GovooBoardTestBase):
    """Issue #51: board pack document generation and per-recipient
    redaction (BR-BOARD-003)."""

    def test_compile_generates_document(self):
        """action_compile() generates and attaches a merged PDF."""
        meeting = self._make_meeting()
        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        pack.action_compile()
        self.assertTrue(pack.document_id, 'Compiling a pack should generate and attach a document.')
        self.assertEqual(pack.state, 'compiled')
        # Regression guard: _render_qweb_pdf returns raw bytes, and
        # ir.attachment.datas expects base64 -- writing the raw bytes
        # directly silently produces an attachment with the right
        # mimetype/name but corrupted, unopenable content.
        #
        # Not asserting a literal %PDF- header here: test mode
        # deliberately substitutes plain HTML for the real wkhtmltopdf
        # render (ir_actions_report.py's own documented fallback, "In
        # case of test environment without enough workers to perform
        # calls to wkhtmltopdf"), and forcing the real renderer via
        # force_report_rendering deadlocks this single-worker test
        # server (wkhtmltopdf calls back into the same blocked HTTP
        # server). Decoding cleanly as UTF-8 and containing the
        # report's own heading is enough to catch the base64 bug either
        # way, without depending on wkhtmltopdf being available.
        content = base64.b64decode(pack.document_id.datas).decode('utf-8')
        self.assertIn(
            'Board Pack', content,
            'The compiled board pack attachment content is corrupted (not valid decoded report output).',
        )

    def test_redaction_is_per_recipient_not_blanket(self):
        """TC-ACC / BR-BOARD-003: two recipients can have different
        redacted sets for the same confidential item, based on their
        own authorization -- not the same list for everyone."""
        meeting = self._make_meeting()
        confidential_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Confidential Matter',
            'item_type': 'discussion',
            'sequence': 1,
            'is_confidential': True,
            'authorized_partner_ids': [(6, 0, [self.partner_a.id])],
        })
        open_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Routine Matter',
            'item_type': 'noting',
            'sequence': 2,
            'is_confidential': False,
        })

        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        pack.action_compile()

        recipient_a = pack.distribution_ids.filtered(lambda d: d.partner_id == self.partner_a)
        recipient_b = pack.distribution_ids.filtered(lambda d: d.partner_id == self.partner_b)

        # partner_a is explicitly authorized: confidential item NOT redacted for them
        self.assertNotIn(confidential_item, recipient_a.redacted_item_ids)
        # partner_b is not authorized: confidential item IS redacted for them
        self.assertIn(confidential_item, recipient_b.redacted_item_ids)
        # the open item is never redacted for anyone
        self.assertNotIn(open_item, recipient_a.redacted_item_ids)
        self.assertNotIn(open_item, recipient_b.redacted_item_ids)

    def test_recipient_document_actually_redacts_content(self):
        """Regression guard: _generate_document()'s stored master copy
        is the SAME single attachment for every recipient and always
        contained every agenda item's full content -- redacted_item_ids
        only ever hid things on the portal's HTML page, never in the
        actual downloadable file. _generate_recipient_document() is
        what a director's download route now actually calls, and it
        must produce genuinely different PDF content per recipient."""
        meeting = self._make_meeting()
        confidential_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Confidential Acquisition Discussion',
            'item_type': 'discussion',
            'sequence': 1,
            'is_confidential': True,
            'authorized_partner_ids': [(6, 0, [self.partner_a.id])],
        })
        open_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Approve Previous Minutes',
            'item_type': 'decision',
            'sequence': 2,
            'is_confidential': False,
        })

        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        pack.action_compile()

        recipient_a = pack.distribution_ids.filtered(lambda d: d.partner_id == self.partner_a)
        recipient_b = pack.distribution_ids.filtered(lambda d: d.partner_id == self.partner_b)

        content_a = pack._generate_recipient_document(recipient_a).decode('utf-8')
        content_b = pack._generate_recipient_document(recipient_b).decode('utf-8')

        # partner_a is authorized: sees the confidential item's own content.
        self.assertIn(confidential_item.title, content_a)
        self.assertIn(open_item.title, content_a)

        # partner_b is not authorized: the confidential item's title/content
        # is genuinely absent from THEIR generated PDF bytes, not merely
        # hidden by a portal page wrapped around the same shared file.
        self.assertNotIn(confidential_item.title, content_b)
        self.assertIn(open_item.title, content_b)

        # The two recipients' actual downloadable files differ.
        self.assertNotEqual(
            content_a, content_b,
            "Two recipients with different authorization must not receive "
            "byte-identical board pack files.",
        )

    def test_merge_agenda_documents_merges_pdf_attachments(self):
        """A supporting document attached to an agenda item -- e.g. the
        previous meeting's signed minutes attached to an "Approval of
        Minutes" item -- must be merged into the pack as real pages,
        not just listed by filename as text (the previous behavior)."""
        meeting = self._make_meeting()
        minutes_pdf = _make_blank_pdf(num_pages=2)
        minutes_attachment = self.env['ir.attachment'].create({
            'name': 'Board Meeting - Q3 2026 - Signed Minutes.pdf',
            'type': 'binary',
            'mimetype': 'application/pdf',
            'datas': base64.b64encode(minutes_pdf),
        })
        item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Approval of Minutes - Previous Meeting',
            'item_type': 'decision',
            'sequence': 1,
            'is_confidential': False,
            'document_ids': [(6, 0, [minutes_attachment.id])],
        })

        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        body_pdf = _make_blank_pdf(num_pages=1)
        merged = pack._merge_agenda_documents(body_pdf, item)

        body_pages = len(PdfFileReader(io.BytesIO(body_pdf)).pages)
        merged_pages = len(PdfFileReader(io.BytesIO(merged)).pages)
        self.assertEqual(
            merged_pages, body_pages + 2,
            "Attaching the previous meeting's minutes to an agenda item "
            "should add its pages to the compiled pack, not just list "
            "its filename as text.",
        )

    def test_merge_agenda_documents_skips_redacted_items(self):
        """_generate_recipient_document() only passes VISIBLE items to
        the merge step -- a confidential item's attachment (e.g. an
        internal due-diligence file) must not be merged into an
        unauthorized recipient's copy either."""
        meeting = self._make_meeting()
        confidential_attachment = self.env['ir.attachment'].create({
            'name': 'Investor Due Diligence Notes.pdf',
            'type': 'binary',
            'mimetype': 'application/pdf',
            'datas': base64.b64encode(_make_blank_pdf(num_pages=3)),
        })
        confidential_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Confidential Matter',
            'item_type': 'discussion',
            'sequence': 1,
            'is_confidential': True,
            'authorized_partner_ids': [(6, 0, [self.partner_a.id])],
            'document_ids': [(6, 0, [confidential_attachment.id])],
        })
        self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Routine Matter',
            'item_type': 'noting',
            'sequence': 2,
            'is_confidential': False,
        })

        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        pack.action_compile()
        recipient_b = pack.distribution_ids.filtered(lambda d: d.partner_id == self.partner_b)
        self.assertIn(confidential_item, recipient_b.redacted_item_ids)

        body_pdf = _make_blank_pdf(num_pages=1)
        visible_items = meeting.agenda_ids.filtered(
            lambda i: i.id not in recipient_b.redacted_item_ids.ids,
        )
        merged = pack._merge_agenda_documents(body_pdf, visible_items)

        merged_pages = len(PdfFileReader(io.BytesIO(merged)).pages)
        self.assertEqual(
            merged_pages, 1,
            "An unauthorized recipient's copy must not gain pages from "
            "a confidential item's attachment.",
        )

    def test_presenter_always_authorized(self):
        """The presenter of a confidential item is always authorized
        for it, even without an explicit authorized_partner_ids entry."""
        meeting = self._make_meeting()
        confidential_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Confidential Matter',
            'item_type': 'discussion',
            'sequence': 1,
            'is_confidential': True,
            'presenter_id': self.partner_a.id,
        })
        self.assertTrue(confidential_item._is_authorized_for(self.partner_a))
        self.assertFalse(confidential_item._is_authorized_for(self.partner_b))

    def test_confidential_item_content_excluded_for_unauthorized_recipient(self):
        """TC-BOARD-003: a confidential agenda item's actual content
        (title) is excluded from what an unauthorized recipient's copy
        shows -- not merely a boolean flag left unused."""
        meeting = self._make_meeting()
        confidential_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Confidential Acquisition Discussion',
            'item_type': 'discussion',
            'sequence': 1,
            'is_confidential': True,
        })
        open_item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Approve Previous Minutes',
            'item_type': 'decision',
            'sequence': 2,
            'is_confidential': False,
        })

        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        pack.action_compile()

        recipient_b = pack.distribution_ids.filtered(lambda d: d.partner_id == self.partner_b)
        visible_items = meeting.agenda_ids - recipient_b.redacted_item_ids
        visible_titles = visible_items.mapped('title')

        self.assertNotIn(
            confidential_item.title, visible_titles,
            'Confidential item\'s title should not appear in an '
            'unauthorized recipient\'s visible content.',
        )
        self.assertIn(open_item.title, visible_titles)
