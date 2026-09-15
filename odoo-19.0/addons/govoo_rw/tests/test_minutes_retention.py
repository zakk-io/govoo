# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'govoo_rw')
class TestMinutesRetentionConfig(TransactionCase):
    """govoo_rw depends on govoo_board, so this is where the real
    govoo.rw.retention -> govoo.minutes.retention_until wiring (BR-BOARD-004)
    can actually be exercised end-to-end."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.committee = cls.env['govoo.committee'].create({
            'name': 'Test Committee',
            'company_id': cls.company.id,
        })
        cls.meeting = cls.env['govoo.meeting'].create({
            'name': 'Test Meeting',
            'committee_id': cls.committee.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 10:00:00',
            'company_id': cls.company.id,
        })

    def test_retention_until_uses_govoo_rw_config_not_literal(self):
        """Changing the seeded retention_years changes new minutes'
        computed retention_until (the compute reads live config at create
        time via a plain search(), not a declared cross-model dependency,
        so it reflects whatever the config was when each record was
        created -- not a retroactive update of already-computed records)."""
        # Seeded default is 10 years (govoo_rw_retention_data.xml)
        minutes_default = self.env['govoo.minutes'].create({
            'meeting_id': self.meeting.id,
            'body': '<p>Minutes.</p>',
        })
        expected_default = minutes_default.create_date.date().replace(
            year=minutes_default.create_date.year + 10,
        )
        self.assertEqual(minutes_default.retention_until, expected_default)

        # Change the seeded rule to 5 years, then create a new minutes record
        rule = self.env.ref('govoo_rw.retention_minutes')
        rule.retention_years = 5

        minutes_updated = self.env['govoo.minutes'].create({
            'meeting_id': self.meeting.id,
            'body': '<p>More minutes.</p>',
        })
        expected_updated = minutes_updated.create_date.date().replace(
            year=minutes_updated.create_date.year + 5,
        )
        self.assertEqual(minutes_updated.retention_until, expected_updated)

    def test_retention_until_falls_back_when_no_active_rule_for_company(self):
        """No active 'minutes' rule for the company -> logged 10-year fallback."""
        other_company = self.env['res.company'].create({'name': 'No Config Co'})
        other_committee = self.env['govoo.committee'].create({
            'name': 'Other Committee',
            'company_id': other_company.id,
        })
        other_meeting = self.env['govoo.meeting'].create({
            'name': 'Other Meeting',
            'committee_id': other_committee.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 10:00:00',
            'company_id': other_company.id,
        })
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': other_meeting.id,
            'body': '<p>Minutes.</p>',
        })
        expected = minutes.create_date.date().replace(
            year=minutes.create_date.year + 10,
        )
        self.assertEqual(minutes.retention_until, expected)
