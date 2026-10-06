# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import date

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class GovooComplianceInstanceCron(models.AbstractModel):
    _name = 'govoo.compliance.cron'
    _description = 'Compliance Cron Engine'

    @api.model
    def _cron_generate_instances(self):
        """Daily: generate upcoming instances from active obligations.

        Each obligation belongs to exactly one company (its own
        advisor-confirmed BR-COMP-001 activation) — only that company
        gets an instance, never every company in the system.
        """
        obligations = self.env['govoo.compliance.obligation'].search([
            ('active', '=', True),
        ])

        for obligation in obligations:
            company = obligation.company_id

            # Skip event-relative (triggered manually)
            if obligation.basis == 'event_relative':
                continue

            # Check entity type filter
            if obligation.applies_to_entity_type != 'all':
                # [CONFIRM] exact matching logic for entity type hierarchy
                if company.govoo_entity_type != obligation.applies_to_entity_type:
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

        Issue #236: the activity itself still requires responsible_id (an
        activity needs someone to assign to), but Company Secretaries are
        notified by real email regardless of whether responsible_id is
        set -- previously an instance with no responsible person got no
        reminder of any kind, silently.
        """
        instances = self.env['govoo.compliance.instance'].search([
            ('state', 'in', ('upcoming', 'in_progress')),
        ])
        template = self.env.ref(
            'govoo_compliance.mail_template_compliance_due_reminder',
            raise_if_not_found=False,
        )

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
                secretaries = self.env['res.users'].get_governance_secretary_partners(
                    extra_partner=instance.responsible_id.partner_id,
                )
                for partner in secretaries:
                    instance.message_post(
                        body=_('Compliance due in %d days: %s') % (
                            days_until, instance.obligation_id.name,
                        ),
                        partner_ids=partner.ids,
                        subtype_xmlid='mail.mt_comment',
                    )
                    if template:
                        template.send_mail(
                            instance.id,
                            email_values={
                                'email_to': partner.email,
                                'recipient_ids': [(6, 0, partner.ids)],
                            },
                            force_send=True,
                        )

    @api.model
    def _cron_escalate_late(self):
        """Daily: transition overdue instances to late, post escalation.

        Issue #236: the message_post below stayed exactly as it was
        (evidence a notification was always intended here) -- it just
        never reached anyone, since nothing subscribes followers to a
        freshly-generated instance. Company Secretaries now also get a
        real email alongside it.
        """
        today = date.today()
        instances = self.env['govoo.compliance.instance'].search([
            ('state', 'in', ('upcoming', 'in_progress')),
            ('due_date', '<', today),
        ])
        template = self.env.ref(
            'govoo_compliance.mail_template_compliance_overdue',
            raise_if_not_found=False,
        )

        for instance in instances:
            instance.write({'state': 'late'})
            # Post escalation message
            instance.message_post(
                body='This compliance instance is now overdue. '
                     'Filing is required as soon as possible.',
                subtype_xmlid='mail.motd',
            )
            for partner in self.env['res.users'].get_governance_secretary_partners():
                instance.message_post(
                    body=_('Compliance is now overdue: %s') % instance.obligation_id.name,
                    partner_ids=partner.ids,
                    subtype_xmlid='mail.mt_comment',
                )
                if template:
                    template.send_mail(
                        instance.id,
                        email_values={
                            'email_to': partner.email,
                            'recipient_ids': [(6, 0, partner.ids)],
                        },
                        force_send=True,
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
