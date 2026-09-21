# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class GovooContractCron(models.AbstractModel):
    """BR-CM-006: contract key-date reminders reuse the exact same
    mail.activity-staging technique as govoo_compliance.cron
    (_cron_send_reminders) -- a daily check that stages a to-do activity
    once a record is within its configured lead time of its due date.
    This is a separate ir.cron entry because it iterates govoo.contract
    rather than govoo.compliance.instance, but it is the same underlying
    mechanism, not a second, parallel reminder engine.
    """
    _name = 'govoo.contract.cron'
    _description = 'Contract Key-Date Reminder Engine'

    @api.model
    def _cron_send_key_date_reminders(self):
        today = fields.Date.context_today(self)
        contracts = self.env['govoo.contract'].search([
            ('state', '=', 'active'),
            ('date_end', '!=', False),
        ])
        for contract in contracts:
            notice_days = contract.contract_type_id.renewal_notice_days or 0
            if not notice_days:
                continue
            days_to_end = (contract.date_end - today).days
            if 0 < days_to_end <= notice_days:
                contract.activity_schedule(
                    activity_type_id=self.env.ref(
                        'mail.mail_activity_data_todo',
                    ).id,
                    summary='Contract "%s" reaches its End Date in %d days' % (
                        contract.name, days_to_end,
                    ),
                    user_id=contract.create_uid.id,
                )
                _logger.info(
                    'Contracts: staged renewal/expiry reminder for "%s" '
                    '(%d days to End Date).',
                    contract.name, days_to_end,
                )

    @api.model
    def _cron_send_obligation_reminders(self):
        """BR-CM-006: obligation due_date reminders, same
        activity_schedule() staging technique -- the other half of the
        reuse the class docstring describes, wired here now that
        govoo.contract.obligation exists (issue #174)."""
        today = fields.Date.context_today(self)
        obligations = self.env['govoo.contract.obligation'].search([
            ('state', 'in', ('open', 'overdue')),
        ])
        for obligation in obligations:
            lead_time = obligation.lead_time_days or 0
            days_to_due = (obligation.due_date - today).days
            if 0 < days_to_due <= lead_time and obligation.responsible_id:
                obligation.activity_schedule(
                    activity_type_id=self.env.ref(
                        'mail.mail_activity_data_todo',
                    ).id,
                    summary='Contract obligation due in %d days: %s' % (
                        days_to_due, obligation.name,
                    ),
                    user_id=obligation.responsible_id.id,
                )
                _logger.info(
                    'Contracts: staged obligation reminder for "%s" '
                    '(%d days to due date).',
                    obligation.name, days_to_due,
                )

    @api.model
    def _cron_escalate_overdue_obligations(self):
        """Daily: delegate to govoo.contract.obligation's own escalation
        method (same underlying engine, not a second one)."""
        self.env['govoo.contract.obligation']._cron_escalate_overdue()
