# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import date

from odoo import api, models

_logger = logging.getLogger(__name__)


class GovooComplianceInstanceCron(models.AbstractModel):
    _name = 'govoo.compliance.cron'
    _description = 'Compliance Cron Engine'

    @api.model
    def _cron_generate_instances(self):
        """Daily: generate upcoming instances from active obligations.

        For each active obligation and each company where it applies,
        compute whether a new instance is due for the current period.
        """
        obligations = self.env['govoo.compliance.obligation'].search([
            ('active', '=', True),
        ])
        companies = self.env['res.company'].search([])

        for obligation in obligations:
            for company in companies:
                # Skip event-relative (triggered manually)
                if obligation.basis == 'event_relative':
                    continue

                # Check entity type filter
                if obligation.applies_to_entity_type != 'all':
                    # [CONFIRM] exact matching logic for entity type hierarchy
                    company_type = company.govoo_entity_type
                    if company_type != obligation.applies_to_entity_type:
                        continue

                # Compute next due date
                due_date = obligation._get_next_due_date(company)
                if not due_date:
                    _logger.warning(
                        'Compliance: Cannot compute due date for obligation "%s" '
                        'company "%s" — missing configuration (e.g. FYE). '
                        'No instance generated.',
                        obligation.name, company.name,
                    )
                    continue

                # Determine period string
                period = self._compute_period(obligation, due_date)

                # Check if instance already exists
                existing = self.env['govoo.compliance.instance'].search([
                    ('obligation_id', '=', obligation.id),
                    ('company_id', '=', company.id),
                    ('period', '=', period),
                ], limit=1)

                if not existing:
                    self.env['govoo.compliance.instance'].create({
                        'obligation_id': obligation.id,
                        'company_id': company.id,
                        'period': period,
                        'due_date': due_date,
                    })
                    _logger.info(
                        'Compliance: Generated instance for "%s" [%s] '
                        'company "%s", due %s.',
                        obligation.name, period, company.name, due_date,
                    )

    @api.model
    def _cron_send_reminders(self):
        """Daily: send staged reminders for upcoming/in_progress instances.

        Creates mail.activity reminders at the obligation's lead_time_days
        offset for responsible users.
        """
        instances = self.env['govoo.compliance.instance'].search([
            ('state', 'in', ('upcoming', 'in_progress')),
        ])

        for instance in instances:
            lead_time = instance.obligation_id.lead_time_days or 0
            days_until = instance.days_to_due

            # Create reminder at lead_time offset
            if 0 < days_until <= lead_time:
                if instance.responsible_id:
                    instance.activity_schedule(
                        activity_type_id=self.env.ref(
                            'mail.mail_activity_data_todo',
                        ).id,
                        summary='Compliance due in %d days: %s' % (
                            days_until, instance.obligation_id.name,
                        ),
                        user_id=instance.responsible_id.id,
                    )

    @api.model
    def _cron_escalate_late(self):
        """Daily: transition overdue instances to late, post escalation."""
        today = date.today()
        instances = self.env['govoo.compliance.instance'].search([
            ('state', 'in', ('upcoming', 'in_progress')),
            ('due_date', '<', today),
        ])

        for instance in instances:
            instance.write({'state': 'late'})
            # Post escalation message
            instance.message_post(
                body='This compliance instance is now overdue. '
                     'Filing is required as soon as possible.',
                subtype_xmlid='mail.motd',
            )
            _logger.warning(
                'Compliance: Instance "%s" [%s] company "%s" is now LATE '
                '(due %s).',
                instance.obligation_id.name,
                instance.period,
                instance.company_id.name,
                instance.due_date,
            )

    @api.model
    def _compute_period(self, obligation, due_date):
        """Compute period string from obligation frequency and due date."""
        if obligation.frequency == 'annual':
            return str(due_date.year)
        if obligation.frequency == 'quarterly':
            quarter = (due_date.month - 1) // 3 + 1
            return '%d-Q%d' % (due_date.year, quarter)
        if obligation.frequency == 'monthly':
            return '%d-%02d' % (due_date.year, due_date.month)
        return str(due_date.year)
