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
