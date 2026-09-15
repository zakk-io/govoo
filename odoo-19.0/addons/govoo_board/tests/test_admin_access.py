# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestBoardAdminReadOnlyAccess(GovooBoardTestBase):
    """access-control.md: Board Administrator's remit is config/users/
    groups only -- read-only on resolution/minutes/board.pack."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = new_test_user(
            cls.env, login='test_board_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=cls.company.id,
        )

    def test_admin_cannot_write_resolution(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        with self.assertRaises(AccessError):
            resolution.with_user(self.admin).write({'title': 'Tampered'})

    def test_admin_cannot_write_minutes(self):
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        with self.assertRaises(AccessError):
            minutes.with_user(self.admin).write({'body': '<p>Tampered.</p>'})

    def test_admin_cannot_write_board_pack(self):
        meeting = self._make_meeting()
        pack = self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        with self.assertRaises(AccessError):
            pack.with_user(self.admin).write({'state': 'compiled'})
