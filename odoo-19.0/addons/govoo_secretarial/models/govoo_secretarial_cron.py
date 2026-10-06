# Part of Govoo. See LICENSE file for full copyright and licensing details.

import logging
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# Issue #236: how many days before a statutory deadline (itself computed
# from a [CONFIRM] ir.config_parameter, see the two _cron_* methods below)
# to start reminding -- this part is an ordinary UX choice, not a legal
# value, so it is a plain constant rather than a second config parameter.
_REMINDER_LOOKAHEAD_DAYS = 7


class GovooSecretarialCron(models.AbstractModel):
    """Statutory-register deadline reminders (issue #236). Neither
    govoo.register.charge nor govoo.register.beneficial.owner had any
    due-date/reminder concept at all before this -- the actual statutory
    day-counts are unconfirmed legal thresholds, so they live as
    ir.config_parameter values (default unset/disabled) rather than
    hard-coded Python literals, same discipline as
    govoo_board.special_resolution_majority_threshold.
    """
    _name = 'govoo.secretarial.cron'
    _description = 'Statutory Register Reminder Engine'

    def _notify_secretaries(self, record, template_xmlid, body):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        for partner in self.env['res.users'].get_governance_secretary_partners():
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
    def _cron_send_charge_registration_reminders(self):
        """A charge must be registered within a statutory window of its
        creation date, or it risks being void against a liquidator/
        creditors later (BR-SEC-STAT-004 context). [CONFIRM]: the exact
        day-count is jurisdiction-specific and unconfirmed -- nothing
        fires until an admin sets
        'govoo_secretarial.charge_registration_deadline_days'.
        """
        deadline_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'govoo_secretarial.charge_registration_deadline_days', '0',
        ) or '0')
        if deadline_days <= 0:
            return
        today = fields.Date.context_today(self)
        charges = self.env['govoo.register.charge'].search([
            ('date_registered', '=', False),
            ('satisfied', '=', False),
            ('date_created', '!=', False),
        ])
        for charge in charges:
            deadline = charge.date_created + relativedelta(days=deadline_days)
            days_to_deadline = (deadline - today).days
            if 0 < days_to_deadline <= _REMINDER_LOOKAHEAD_DAYS:
                self._notify_secretaries(
                    charge,
                    'govoo_secretarial.mail_template_charge_registration_reminder',
                    _('Charge against %s must be registered within %d days.') % (
                        charge.chargee_partner_id.name or charge.id, days_to_deadline,
                    ),
                )
                _logger.info(
                    'Secretarial: staged charge registration reminder for '
                    'charge #%d (%d days to deadline).', charge.id, days_to_deadline,
                )

    @api.model
    def _cron_send_beneficial_owner_declaration_reminders(self):
        """A new beneficial owner must be declared/filed within a
        statutory window of becoming registrable. [CONFIRM]: the exact
        day-count is jurisdiction-specific and unconfirmed -- nothing
        fires until an admin sets
        'govoo_secretarial.beneficial_owner_declaration_deadline_days'.
        """
        deadline_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'govoo_secretarial.beneficial_owner_declaration_deadline_days', '0',
        ) or '0')
        if deadline_days <= 0:
            return
        today = fields.Date.context_today(self)
        owners = self.env['govoo.register.beneficial.owner'].search([
            ('evidence_document_id', '=', False),
            ('date_became_registrable', '!=', False),
        ])
        for owner in owners:
            deadline = owner.date_became_registrable + relativedelta(days=deadline_days)
            days_to_deadline = (deadline - today).days
            if 0 < days_to_deadline <= _REMINDER_LOOKAHEAD_DAYS:
                self._notify_secretaries(
                    owner,
                    'govoo_secretarial.mail_template_beneficial_owner_declaration_reminder',
                    _('Beneficial ownership declaration for %s must be filed within %d days.') % (
                        owner.partner_id.name, days_to_deadline,
                    ),
                )
                _logger.info(
                    'Secretarial: staged beneficial owner declaration reminder '
                    'for #%d (%d days to deadline).', owner.id, days_to_deadline,
                )
