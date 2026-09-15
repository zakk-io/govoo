# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestMultiCompanyIsolation(TransactionCase):
    """TC-SEC-002 / TC-SEC-002b: a Company-X-only user cannot read/list or
    directly browse-by-ID a Company-Y record, across models from multiple
    modules. Not exhaustive over every model in data-model/entities.md
    (impractical as a single scenario) -- representative sample instead."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_x = cls.env.company
        cls.company_y = cls.env['res.company'].create({'name': 'Company Y'})
        cls.user_x = new_test_user(
            cls.env, login='test_company_x_user',
            groups='govoo_base.group_govoo_user',
            company_id=cls.company_x.id,
        )

    def _assert_isolated(self, model_name, y_record):
        Model = self.env[model_name].with_user(self.user_x)
        self.assertNotIn(y_record, Model.search([]))
        with self.assertRaises(AccessError, msg=f'{model_name}: browse-by-ID should be denied'):
            y_record.with_user(self.user_x).check_access('read')

    def test_committee_isolated_across_companies(self):
        committee_y = self.env['govoo.committee'].create({
            'name': 'Company Y Committee',
            'company_id': self.company_y.id,
        })
        self._assert_isolated('govoo.committee', committee_y)

    def test_appointment_isolated_across_companies(self):
        partner = self.env['res.partner'].create({'name': 'Company Y Person'})
        appointment_y = self.env['govoo.appointment'].create({
            'partner_id': partner.id,
            'company_id': self.company_y.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        self._assert_isolated('govoo.appointment', appointment_y)

    def test_meeting_isolated_across_companies(self):
        """govoo_board isn't a govoo_base dependency -- skips cleanly when
        run against govoo_base alone, runs for real whenever govoo_board
        is also installed (e.g. the full-stack test run)."""
        if 'govoo.meeting' not in self.env:
            self.skipTest('govoo_board not installed')
        committee_y = self.env['govoo.committee'].create({
            'name': 'Company Y Committee for Meeting',
            'company_id': self.company_y.id,
        })
        meeting_y = self.env['govoo.meeting'].create({
            'name': 'Company Y Meeting',
            'committee_id': committee_y.id,
            'meeting_type': 'committee',
            'date': '2026-01-01 10:00:00',
            'company_id': self.company_y.id,
        })
        self._assert_isolated('govoo.meeting', meeting_y)

    def test_share_class_isolated_across_companies(self):
        """govoo_shares isn't a govoo_base dependency -- see note above."""
        if 'govoo.share.class' not in self.env:
            self.skipTest('govoo_shares not installed')
        share_class_y = self.env['govoo.share.class'].create({
            'name': 'Company Y Shares',
            'nominal_value': 100,
            'total_authorised': 1000,
            'company_id': self.company_y.id,
        })
        self._assert_isolated('govoo.share.class', share_class_y)
