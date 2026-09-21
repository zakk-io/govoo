# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo.fields import Date
from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestKeyDateReminders(GovooContractsTestBase):
    """Key-Date Tracking & Reminder Integration (issue #173): BR-CM-006.

    Reuses the same mail.activity-staging technique as
    govoo_compliance.cron, via a new govoo.contract.cron entry point
    (a new ir.cron row is unavoidable since it iterates a different
    model, but it is not a second reminder mechanism).
    """

    def _active_contract(self, date_end):
        self._grant_delegation()
        contract = self._make_contract(date_end=date_end)
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        contract.action_activate()
        return contract

    def test_reminder_staged_within_notice_window(self):
        self.contract_type.renewal_notice_days = 30
        contract = self._active_contract(Date.today() + timedelta(days=10))
        self.env['govoo.contract.cron']._cron_send_key_date_reminders()
        self.assertTrue(contract.activity_ids)

    def test_no_reminder_outside_notice_window(self):
        self.contract_type.renewal_notice_days = 30
        contract = self._active_contract(Date.today() + timedelta(days=90))
        self.env['govoo.contract.cron']._cron_send_key_date_reminders()
        self.assertFalse(contract.activity_ids)

    def test_no_reminder_when_notice_days_not_configured(self):
        contract = self._active_contract(Date.today() + timedelta(days=10))
        self.env['govoo.contract.cron']._cron_send_key_date_reminders()
        self.assertFalse(contract.activity_ids)

    def test_no_reminder_for_non_active_contract(self):
        self.contract_type.renewal_notice_days = 30
        self._grant_delegation()
        contract = self._make_contract(date_end=Date.today() + timedelta(days=10))
        # still in draft -- not yet active
        self.env['govoo.contract.cron']._cron_send_key_date_reminders()
        self.assertFalse(contract.activity_ids)
