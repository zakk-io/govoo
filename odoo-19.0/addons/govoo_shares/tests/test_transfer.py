# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class GovooShareTransferTC(GovooShareTestBase):
    """TC-SHARE-002, 005 — Transfer state machine and GL hook."""

    def test_transfer_state_machine(self):
        """Transfer advances draft → approved → registered."""
        self._make_allotment(self.partner_a, 10)
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 5,
            'date_transferred': '2026-03-01',
        })
        self.assertEqual(transfer.state, 'draft')
        transfer.action_approve()
        self.assertEqual(transfer.state, 'approved')
        transfer.action_register()
        self.assertEqual(transfer.state, 'registered')

    def test_no_gl_posting_by_default(self):
        """TC-SHARE-005: No account.move created when GL hook is off."""
        self._make_allotment(self.partner_a, 10)
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 5,
            'date_transferred': '2026-03-01',
        })
        transfer.action_approve()
        transfer.action_register()

        # No account.move should exist for this transfer
        # Guard: account module may not be installed
        account_installed = self.env['ir.module.module'].search_count([
            ('name', '=', 'account'),
            ('state', '=', 'installed'),
        ])
        if account_installed:
            moves = self.env['account.move'].search([
                ('ref', 'ilike', '%share%transfer%'),
            ])
            self.assertFalse(moves)

    def test_same_party_transfer_raises(self):
        """Transferor and transferee must differ."""
        with self.assertRaises(Exception):
            self.env['govoo.share.transfer'].create({
                'share_class_id': self.share_class.id,
                'transferor_id': self.partner_a.id,
                'transferee_id': self.partner_a.id,
                'quantity': 5,
                'date_transferred': '2026-03-01',
            })
