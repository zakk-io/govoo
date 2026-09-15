# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooBoardReportsTC(GovooBoardTestBase):
    """Issue #121: report_minutes/report_resolution_summary set 'o' to
    rendered text instead of the record, crashing web.external_layout.
    These tests actually render each report's PDF so a regression here
    is caught automatically."""

    def test_minutes_report_renders(self):
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        report = self.env.ref('govoo_board.action_report_govoo_minutes')
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report.id, minutes.ids,
        )
        self.assertTrue(pdf_content)

    def test_resolution_summary_report_renders(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        report = self.env.ref('govoo_board.action_report_govoo_resolution_summary')
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report.id, resolution.ids,
        )
        self.assertTrue(pdf_content)
