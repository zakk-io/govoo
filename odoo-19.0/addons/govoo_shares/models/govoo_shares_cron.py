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


class GovooSharesCron(models.AbstractModel):
    """Share register deadline reminders (issue #236). Neither
    govoo.share.allotment nor govoo.share.transfer had any due-date/
    reminder concept at all before this -- the actual statutory
    day-counts are unconfirmed legal thresholds, so they live as
    ir.config_parameter values (default unset/disabled) rather than
    hard-coded Python literals, same discipline as
    govoo_board.special_resolution_majority_threshold.
    """
    _name = 'govoo.shares.cron'
    _description = 'Share Register Reminder Engine'

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
    def _cron_send_certificate_issuance_reminders(self):
        """A share certificate must be issued to the shareholder within a
        statutory window of allotment. [CONFIRM]: the exact day-count is
        jurisdiction-specific and unconfirmed -- nothing fires until an
        admin sets 'govoo_shares.certificate_issuance_deadline_days'.
        """
        deadline_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'govoo_shares.certificate_issuance_deadline_days', '0',
        ) or '0')
        if deadline_days <= 0:
            return
        today = fields.Date.context_today(self)
        allotments = self.env['govoo.share.allotment'].search([
            ('certificate_document_id', '=', False),
            ('date_allotted', '!=', False),
        ])
        for allotment in allotments:
            deadline = allotment.date_allotted + relativedelta(days=deadline_days)
            days_to_deadline = (deadline - today).days
            if 0 < days_to_deadline <= _REMINDER_LOOKAHEAD_DAYS:
                self._notify_secretaries(
                    allotment,
                    'govoo_shares.mail_template_certificate_issuance_reminder',
                    _('Share certificate for %s (allotment #%d) must be issued within %d days.') % (
                        allotment.partner_id.name, allotment.id, days_to_deadline,
                    ),
                )
                _logger.info(
                    'Shares: staged certificate issuance reminder for allotment '
                    '#%d (%d days to deadline).', allotment.id, days_to_deadline,
                )

    @api.model
    def _cron_send_transfer_registration_reminders(self):
        """A share transfer must be registered (and any stamp duty paid)
        within a statutory window of the transfer date. [CONFIRM]: the
        exact day-count is jurisdiction-specific and unconfirmed --
        nothing fires until an admin sets
        'govoo_shares.transfer_registration_deadline_days'.
        """
        deadline_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'govoo_shares.transfer_registration_deadline_days', '0',
        ) or '0')
        if deadline_days <= 0:
            return
        today = fields.Date.context_today(self)
        transfers = self.env['govoo.share.transfer'].search([
            ('state', '!=', 'registered'),
            ('date_transferred', '!=', False),
        ])
        for transfer in transfers:
            deadline = transfer.date_transferred + relativedelta(days=deadline_days)
            days_to_deadline = (deadline - today).days
            if 0 < days_to_deadline <= _REMINDER_LOOKAHEAD_DAYS:
                self._notify_secretaries(
                    transfer,
                    'govoo_shares.mail_template_transfer_registration_reminder',
                    _('Share transfer from %s to %s must be registered within %d days.') % (
                        transfer.transferor_id.name, transfer.transferee_id.name, days_to_deadline,
                    ),
                )
                _logger.info(
                    'Shares: staged transfer registration reminder for transfer '
                    '#%d (%d days to deadline).', transfer.id, days_to_deadline,
                )
