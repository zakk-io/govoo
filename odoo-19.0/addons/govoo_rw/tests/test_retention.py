# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'govoo_rw')
class TestRwRetention(TransactionCase):
    """govoo.rw.retention._get_expired_records / _cron_check_disposal."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.board_reports_rule = cls.env['govoo.rw.retention'].create({
            'name': 'Board Reports Retention',
            'retention_category': 'board_reports',
            'basis': 'periods',
            'retention_periods': 1,
            'company_id': cls.company.id,
        })

    def test_board_reports_has_no_backing_model(self):
        """board_reports has no document model; must return an empty recordset,
        not scan mail.message or raise."""
        expired = self.env['govoo.rw.retention']._get_expired_records(
            self.board_reports_rule, date.today(),
        )
        self.assertFalse(expired)
        self.assertEqual(expired._name, 'govoo.rw.retention')

    def test_cron_check_disposal_noops_for_board_reports(self):
        """The weekly cron runs cleanly with only a board_reports rule active.

        Other seeded categories (accounts/auditor_reports) map to
        account.move, which isn't installed in this test's dependency
        set -- deactivated here to isolate the board_reports path this
        test (and issue #40) is about.
        """
        other_rules = self.env['govoo.rw.retention'].search([
            ('id', '!=', self.board_reports_rule.id),
        ])
        other_rules.write({'active': False})
        self.env['govoo.rw.retention']._cron_check_disposal()

    def _make_expired_minutes(self, company):
        committee = self.env['govoo.committee'].create({
            'name': 'Committee %s' % company.name,
            'company_id': company.id,
        })
        meeting = self.env['govoo.meeting'].create({
            'name': 'Meeting %s' % company.name,
            'committee_id': committee.id,
            'meeting_type': 'committee',
            'date': '2020-01-01 10:00:00',
            'company_id': company.id,
        })
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        # Bypass the action/validation chain -- only the resulting state and
        # an old create_date matter for this cron's domain, not how the
        # record got there.
        minutes.write({'state': 'approved'})
        self.env.cr.execute(
            "UPDATE govoo_minutes SET create_date = %s WHERE id = %s",
            ('2020-01-01', minutes.id),
        )
        minutes.invalidate_recordset(['create_date'])
        return minutes

    def test_expired_records_scoped_to_rule_company(self):
        """A Company A retention rule must never flag Company B's records."""
        company_b = self.env['res.company'].create({'name': 'Other Company'})
        minutes_a = self._make_expired_minutes(self.company)
        minutes_b = self._make_expired_minutes(company_b)

        rule_a = self.env['govoo.rw.retention'].create({
            'name': 'Minutes Retention A',
            'retention_category': 'minutes',
            'basis': 'years',
            'retention_years': 1,
            'company_id': self.company.id,
        })

        expired = self.env['govoo.rw.retention']._get_expired_records(rule_a, date.today())
        self.assertIn(minutes_a, expired)
        self.assertNotIn(minutes_b, expired)

    def _make_expired_resolution(self, state):
        committee = self.env['govoo.committee'].create({
            'name': 'Resolution Test Committee',
            'company_id': self.company.id,
        })
        meeting = self.env['govoo.meeting'].create({
            'name': 'Resolution Test Meeting',
            'committee_id': committee.id,
            'meeting_type': 'committee',
            'date': '2020-01-01 10:00:00',
            'company_id': self.company.id,
        })
        resolution = self.env['govoo.resolution'].create({
            'title': 'Old Resolution',
            'resolution_type': 'ordinary',
            'meeting_id': meeting.id,
        })
        # Bypass the action/validation chain -- only the resulting state and
        # an old create_date matter for this cron's domain.
        resolution.write({'state': state})
        self.env.cr.execute(
            "UPDATE govoo_resolution SET create_date = %s WHERE id = %s",
            ('2020-01-01', resolution.id),
        )
        resolution.invalidate_recordset(['create_date'])
        return resolution

    def test_resolutions_use_terminal_state_not_approved(self):
        """govoo.resolution has no 'approved' state; the disposal check
        must filter on an actual terminal state (passed/failed/withdrawn)."""
        resolution = self._make_expired_resolution('passed')
        rule = self.env['govoo.rw.retention'].create({
            'name': 'Resolutions Retention',
            'retention_category': 'resolutions',
            'basis': 'years',
            'retention_years': 1,
            'company_id': self.company.id,
        })
        expired = self.env['govoo.rw.retention']._get_expired_records(rule, date.today())
        self.assertIn(resolution, expired)
