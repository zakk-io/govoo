# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models

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

    def _notify_secretaries(self, record, template_xmlid, body, extra_partner=None):
        """Issue #236: every reminder below only ever staged an internal
        activity, which never reached anyone as an actual email -- every
        active Company Secretary (plus extra_partner, e.g. an obligation's
        own responsible_id, if given) now also gets a real email + in-app
        chatter notification, on top of whatever activity already fires."""
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        secretaries = self.env['res.users'].get_governance_secretary_partners(
            extra_partner=extra_partner,
        )
        for partner in secretaries:
            record.message_post(
                body=body, partner_ids=partner.ids, subtype_xmlid='mail.mt_comment',
            )
            if template:
                template.send_mail(
                    record.id,
                    email_values={
                        'email_to': partner.email,
                        'recipient_ids': [(6, 0, partner.ids)],
                    },
                    force_send=True,
                )

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
                self._notify_secretaries(
                    contract,
                    'govoo_contracts.mail_template_contract_key_date_reminder',
                    _('Contract "%s" reaches its End Date in %d days.') % (
                        contract.name, days_to_end,
                    ),
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
        govoo.contract.obligation exists (issue #174).

        Issue #236: the activity itself still requires responsible_id (an
        activity needs someone to assign to), but Company Secretaries are
        notified by real email regardless of whether responsible_id is
        set -- previously an obligation with no responsible person got no
        reminder of any kind, silently.
        """
        today = fields.Date.context_today(self)
        obligations = self.env['govoo.contract.obligation'].search([
            ('state', 'in', ('open', 'overdue')),
        ])
        for obligation in obligations:
            lead_time = obligation.lead_time_days or 0
            days_to_due = (obligation.due_date - today).days
            if 0 < days_to_due <= lead_time:
                if obligation.responsible_id:
                    obligation.activity_schedule(
                        activity_type_id=self.env.ref(
                            'mail.mail_activity_data_todo',
                        ).id,
                        summary='Contract obligation due in %d days: %s' % (
                            days_to_due, obligation.name,
                        ),
                        user_id=obligation.responsible_id.id,
                    )
                self._notify_secretaries(
                    obligation,
                    'govoo_contracts.mail_template_contract_obligation_reminder',
                    _('Contract obligation due in %d days: %s') % (
                        days_to_due, obligation.name,
                    ),
                    extra_partner=obligation.responsible_id.partner_id,
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

    @api.model
    def _cron_expire_fixed_term_contracts(self):
        """FR-CM-14/TC-CM-010: fixed-term contracts past date_end
        transition to 'expired'. Evergreen (renewal_type='auto')
        contracts are explicitly excluded and stay active until
        explicitly terminated -- the whole point of the distinction.

        Issue #236: this previously produced zero notification of any
        kind (not even an internal activity) -- Company Secretaries now
        get a real email per newly-expired contract.
        """
        today = fields.Date.context_today(self)
        contracts = self.env['govoo.contract'].search([
            ('state', '=', 'active'),
            ('renewal_type', '=', 'fixed'),
            ('date_end', '!=', False),
            ('date_end', '<', today),
        ])
        if contracts:
            contracts.action_expire()
            for contract in contracts:
                self._notify_secretaries(
                    contract,
                    'govoo_contracts.mail_template_contract_expired',
                    _('Contract "%s" has expired.') % contract.name,
                )
            _logger.info(
                'Contracts: auto-expired %d fixed-term contract(s) past '
                'their End Date.', len(contracts),
            )
