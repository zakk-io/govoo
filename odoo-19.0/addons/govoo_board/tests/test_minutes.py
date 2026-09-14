# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestGovooMinutesRetention(GovooBoardTestBase):
    """govoo_board does not depend on govoo_rw; this suite only exercises
    the fallback path (BR-BOARD-004). The real govoo.rw.retention lookup
    is covered in govoo_rw's own tests, which do depend on govoo_board."""

    def test_retention_until_falls_back_to_ten_years_without_govoo_rw(self):
        """Without govoo_rw installed, retention_until defaults to 10 years."""
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        self.assertTrue('govoo.rw.retention' not in self.env)
        expected = minutes.create_date.date().replace(
            year=minutes.create_date.year + 10,
        )
        self.assertEqual(minutes.retention_until, expected)
