# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestCommunityFallback(GovooBoardTestBase):
    """TC-SEC-009: with Documents/Sign not installed (Community, the
    default in this test environment), board pack compile/distribute
    completes via the ir.attachment fallback without an unhandled error."""

    def test_board_pack_compile_and_distribute_without_enterprise_apps(self):
        self.assertFalse(
            self.env['ir.module.module'].sudo().search([
                ('name', 'in', ('documents', 'sign')),
                ('state', '=', 'installed'),
            ]),
            'This test assumes Documents/Sign are not installed (Community).',
        )
        meeting = self._make_meeting()
        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        pack.action_compile()
        self.assertEqual(pack.state, 'compiled')
        pack.action_distribute()
        self.assertEqual(pack.state, 'distributed')
