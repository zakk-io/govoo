# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


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
