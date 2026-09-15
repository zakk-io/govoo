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
