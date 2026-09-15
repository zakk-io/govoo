# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestMeetingStatButtons(GovooBoardTestBase):
    """Test meeting stat buttons and computed count fields."""

    def test_agenda_count(self):
        """Meeting agenda_count computes correctly."""
        meeting = self._make_meeting()
        self.assertEqual(meeting.agenda_count, 0)
        self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Approval of Previous Minutes',
            'item_type': 'discussion',
            'sequence': 1,
        })
        meeting.invalidate_recordset(['agenda_count'])
        self.assertEqual(meeting.agenda_count, 1)

    def test_pack_count(self):
        """Meeting pack_count is 1 when pack exists, 0 otherwise."""
        meeting = self._make_meeting()
        self.assertEqual(meeting.pack_count, 0)
        pack = self.env['govoo.board.pack'].create({
            'meeting_id': meeting.id,
        })
        meeting.invalidate_recordset(['pack_count'])
        self.assertEqual(meeting.pack_count, 1)

    def test_minutes_count(self):
        """Meeting minutes_count is 1 when minutes exists, 0 otherwise."""
        meeting = self._make_meeting()
        self.assertEqual(meeting.minutes_count, 0)
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Test minutes.</p>',
        })
        meeting.minutes_id = minutes
        meeting.invalidate_recordset(['minutes_count'])
        self.assertEqual(meeting.minutes_count, 1)

    def test_resolution_count(self):
        """Meeting resolution_count computes correctly."""
        meeting = self._make_meeting()
        self.assertEqual(meeting.resolution_count, 0)
        self._make_resolution(meeting)
        meeting.invalidate_recordset(['resolution_count'])
        self.assertEqual(meeting.resolution_count, 1)

    def test_action_view_agenda(self):
        """action_view_agenda returns correct action."""
        meeting = self._make_meeting()
        action = meeting.action_view_agenda()
        self.assertEqual(action['res_model'], 'govoo.agenda.item')
        self.assertEqual(action['domain'], [('meeting_id', '=', meeting.id)])

    def test_action_view_pack(self):
        """action_view_pack returns correct action when pack exists."""
        meeting = self._make_meeting()
        pack = self.env['govoo.board.pack'].create({
            'meeting_id': meeting.id,
        })
        action = meeting.action_view_pack()
        self.assertEqual(action['res_model'], 'govoo.board.pack')
        self.assertEqual(action['res_id'], pack.id)

    def test_action_view_pack_returns_false_when_no_pack(self):
        """action_view_pack returns False when no pack."""
        meeting = self._make_meeting()
        self.assertFalse(meeting.action_view_pack())

    def test_action_view_minutes(self):
        """action_view_minutes returns correct action when minutes exist."""
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Test minutes.</p>',
        })
        meeting.minutes_id = minutes
        action = meeting.action_view_minutes()
        self.assertEqual(action['res_model'], 'govoo.minutes')
        self.assertEqual(action['res_id'], minutes.id)

    def test_action_view_minutes_returns_false_when_no_minutes(self):
        """action_view_minutes returns False when no minutes."""
        meeting = self._make_meeting()
        self.assertFalse(meeting.action_view_minutes())

    def test_action_view_resolutions(self):
        """action_view_resolutions returns correct action."""
        meeting = self._make_meeting()
        action = meeting.action_view_resolutions()
        self.assertEqual(action['res_model'], 'govoo.resolution')
        self.assertEqual(action['domain'], [('meeting_id', '=', meeting.id)])


@tagged('post_install', '-at_install')
class TestResolutionStatButtons(GovooBoardTestBase):
    """Test resolution stat buttons and computed count fields."""

    def test_vote_count(self):
        """Resolution vote_count computes correctly."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self.assertEqual(resolution.vote_count, 0)
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        resolution.invalidate_recordset(['vote_count'])
        self.assertEqual(resolution.vote_count, 1)

    def test_action_view_votes(self):
        """action_view_votes returns correct action."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        action = resolution.action_view_votes()
        self.assertEqual(action['res_model'], 'govoo.vote')
        self.assertEqual(action['domain'], [('resolution_id', '=', resolution.id)])
