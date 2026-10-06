# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class TestGovooGovernanceConfig(GovooBoardTestBase):
    """Issue #238: a secretary-editable page for the [CONFIRM] legal
    thresholds that previously only existed as bare ir.config_parameter
    keys, reachable only via Settings > Technical > System Parameters."""

    def _get_param(self, key):
        return self.env['ir.config_parameter'].sudo().get_param(key)

    def test_create_seeds_safe_defaults(self):
        record = self.env['govoo.governance.config'].create({
            'company_id': self.company.id,
        })
        self.assertEqual(record.charge_registration_deadline_days, 0)
        self.assertFalse(record.e_signature_legally_confirmed)
        self.assertEqual(record.minutes_retention_default_years, 10)

    def test_write_pushes_values_to_matching_config_parameters(self):
        record = self.env['govoo.governance.config'].create({
            'company_id': self.company.id,
        })
        record.write({
            'charge_registration_deadline_days': 21,
            'beneficial_owner_declaration_deadline_days': 14,
            'certificate_issuance_deadline_days': 60,
            'transfer_registration_deadline_days': 30,
            'e_signature_legally_confirmed': True,
            'minutes_retention_default_years': 15,
        })
        self.assertEqual(self._get_param('govoo_secretarial.charge_registration_deadline_days'), '21')
        self.assertEqual(self._get_param('govoo_secretarial.beneficial_owner_declaration_deadline_days'), '14')
        self.assertEqual(self._get_param('govoo_shares.certificate_issuance_deadline_days'), '60')
        self.assertEqual(self._get_param('govoo_shares.transfer_registration_deadline_days'), '30')
        self.assertEqual(self._get_param('govoo_board.e_signature_legally_confirmed'), 'True')
        self.assertEqual(self._get_param('govoo_board.minutes_retention_default_years'), '15')

    def test_integer_field_back_to_zero_clears_the_parameter(self):
        """0 means "disabled", matching the existing crons' own
        `if not deadline_days: return` guard -- it must clear the
        parameter, not persist the literal string "0"."""
        record = self.env['govoo.governance.config'].create({
            'company_id': self.company.id,
            'charge_registration_deadline_days': 21,
        })
        self.assertEqual(self._get_param('govoo_secretarial.charge_registration_deadline_days'), '21')
        record.write({'charge_registration_deadline_days': 0})
        self.assertFalse(self._get_param('govoo_secretarial.charge_registration_deadline_days'))

    def test_get_or_create_seeds_from_a_preexisting_system_parameter(self):
        """An admin who already set a value directly via System Parameters
        before this UI existed must see it reflected, not reset to 0/False."""
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_shares.certificate_issuance_deadline_days', '45',
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        record = self.env['govoo.governance.config']._get_or_create_for_company(self.company)
        self.assertEqual(record.certificate_issuance_deadline_days, 45)
        self.assertTrue(record.e_signature_legally_confirmed)
        # Untouched params still fall back to their safe defaults.
        self.assertEqual(record.charge_registration_deadline_days, 0)
        self.assertEqual(record.minutes_retention_default_years, 10)

    def test_get_or_create_is_idempotent_per_company(self):
        Config = self.env['govoo.governance.config']
        first = Config._get_or_create_for_company(self.company)
        second = Config._get_or_create_for_company(self.company)
        self.assertEqual(first, second)

    def test_only_one_record_per_company(self):
        self.env['govoo.governance.config'].create({'company_id': self.company.id})
        with self.assertRaises(Exception):
            self.env['govoo.governance.config'].create({'company_id': self.company.id})

    def test_minutes_retention_must_be_positive(self):
        record = self.env['govoo.governance.config'].create({
            'company_id': self.company.id,
        })
        with self.assertRaises(ValidationError):
            record.write({'minutes_retention_default_years': 0})

    def test_minutes_retention_default_feeds_retention_until(self):
        """Raising the configured retention period here changes new
        minutes' computed retention_until (govoo_minutes.py), when no
        active govoo_rw retention rule overrides it (govoo_rw is
        authoritative when present -- BR-BOARD-004 -- so any such rule
        in this shared dev database must be deactivated first)."""
        if 'govoo.rw.retention' in self.env:
            self.env['govoo.rw.retention'].search([
                ('retention_category', '=', 'minutes'),
                ('company_id', '=', self.company.id),
            ]).write({'active': False})
        self.env['govoo.governance.config'].create({
            'company_id': self.company.id,
            'minutes_retention_default_years': 20,
        })
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        expected = minutes.create_date.date().replace(
            year=minutes.create_date.year + 20,
        )
        self.assertEqual(minutes.retention_until, expected)

    def test_secretary_can_configure_but_user_cannot(self):
        secretary = new_test_user(
            self.env, login='test_governance_config_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        plain_user = new_test_user(
            self.env, login='test_governance_config_user',
            groups='govoo_base.group_govoo_user',
            company_id=self.company.id,
        )
        record = self.env['govoo.governance.config'].with_user(secretary).create({
            'company_id': self.company.id,
        })
        record.with_user(secretary).write({'charge_registration_deadline_days': 10})
        with self.assertRaises(AccessError):
            record.with_user(plain_user).write({'charge_registration_deadline_days': 5})
