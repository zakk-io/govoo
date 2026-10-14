# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase

# Every govoo_board governance-policy switch introduced by #269/#271, all
# "unset = original behavior" by design. This module's tests run against
# the same persistent dev database real users configure live via
# Governance Settings (this project has no separate, disposable test DB)
# -- whatever a Secretary has actually turned on for real (e.g. while
# manually testing the feature) is otherwise still committed and visible
# as the starting state of every test transaction, silently breaking any
# test that doesn't itself account for that specific parameter. Clearing
# all of them before each test keeps the suite hermetic regardless of
# what's configured live; TransactionCase rolls this back afterward, so a
# real admin's live configuration is untouched once the test run ends.
_GOVOO_BOARD_CONFIG_PARAMS_TO_RESET = (
    'govoo_board.special_resolution_majority_threshold',
    'govoo_board.resolution_voting_window_days',
    'govoo_board.resolution_notice_period_days',
    'govoo_board.resolution_meeting_state_gate_enabled',
    'govoo_board.resolution_tie_break_enabled',
    'govoo_board.written_resolution_quorum_percentage',
    'govoo_board.meeting_notice_period_days',
    'govoo_board.minutes_require_different_approver',
    'govoo_board.board_pack_min_lead_days',
    'govoo_board.agenda_freeze_on_schedule',
    'govoo_board.meeting_close_requires_minutes_approved',
)


class GovooBoardTestBase(TransactionCase):
    """Shared setup for board module tests."""

    def setUp(self):
        super().setUp()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        for key in _GOVOO_BOARD_CONFIG_PARAMS_TO_RESET:
            IrConfigParameter.set_param(key, False)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Director A',
            'company_id': cls.company.id,
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Director B',
            'company_id': cls.company.id,
        })
        cls.partner_c = cls.env['res.partner'].create({
            'name': 'Director C',
            'company_id': cls.company.id,
        })
        cls.partner_d = cls.env['res.partner'].create({
            'name': 'Director D',
            'company_id': cls.company.id,
        })
        cls.committee = cls.env['govoo.committee'].create({
            'name': 'Board of Directors',
            'company_id': cls.company.id,
        })
        # Create appointments for directors
        for i, partner in enumerate([cls.partner_a, cls.partner_b, cls.partner_c, cls.partner_d], 1):
            cls.env['govoo.appointment'].create({
                'partner_id': partner.id,
                'company_id': cls.company.id,
                'role': 'director',
                'committee_id': cls.committee.id,
                'date_appointed': '2025-01-01',
            })

    def _make_meeting(self, quorum=3):
        """Create a board meeting with 4 attendees."""
        return self.env['govoo.meeting'].create({
            'name': 'Board Meeting Q1',
            'meeting_type': 'board',
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'quorum_required': quorum,
            'attendee_ids': [(6, 0, [
                self.partner_a.id,
                self.partner_b.id,
                self.partner_c.id,
                self.partner_d.id,
            ])],
            'company_id': self.company.id,
        })

    def _make_resolution(self, meeting, resolution_type='ordinary'):
        """Create a resolution linked to a meeting."""
        return self.env['govoo.resolution'].create({
            'title': 'Resolution to approve minutes',
            'text': '<p>Resolved that the minutes of the previous meeting be approved.</p>',
            'resolution_type': resolution_type,
            'meeting_id': meeting.id,
        })
