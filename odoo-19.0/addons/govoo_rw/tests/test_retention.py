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
