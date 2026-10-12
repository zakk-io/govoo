# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestBoardViewRendering(GovooBoardTestBase):
    """Issue #253: get_views() exercises the same field/widget validation
    Odoo runs on module upgrade, so a ribbon or tooltip referencing a
    renamed/typo'd field would fail here too, not just at -u time."""

    def test_meeting_form_view_loads_when_closed(self):
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Test minutes.</p>',
        })
        minutes.action_submit_for_approval()
        meeting.minutes_id = minutes
        meeting.action_minute()
        meeting.action_close()
        self.assertEqual(meeting.state, 'closed')
        meeting.get_views([(False, 'form')])

    def test_resolution_form_view_loads_when_failed(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        for partner in [self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'against',
            })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'failed')
        resolution.get_views([(False, 'form')])

    def test_resolution_form_view_loads_when_withdrawn(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_withdraw()
        self.assertEqual(resolution.state, 'withdrawn')
        resolution.get_views([(False, 'form')])

    def test_resolution_votes_smart_button_reaches_kanban(self):
        """Issue #251 regression: action_view_votes() must offer kanban
        first, not just list/form, or the smart button can never reach the
        redesigned vote kanban."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        action = resolution.action_view_votes()
        self.assertEqual(action['view_mode'].split(',')[0], 'kanban')
