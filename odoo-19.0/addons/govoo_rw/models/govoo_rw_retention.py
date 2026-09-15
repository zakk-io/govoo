# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooRwRetention(models.Model):
    _name = 'govoo.rw.retention'
    _description = 'Document Retention Configuration'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(
        string='Retention Rule Name',
        required=True,
        tracking=True,
    )
    retention_category = fields.Selection(
        selection=[
            ('minutes', 'Minutes'),
            ('resolutions', 'Resolutions'),
            ('accounts', 'Accounts'),
            ('auditor_reports', 'Auditor Reports'),
            ('board_reports', 'Board Reports'),
        ],
        string='Retention Category',
        required=True,
        tracking=True,
        help='The type of document this retention rule applies to.',
    )
    retention_years = fields.Integer(
        string='Retention Period (Years)',
        tracking=True,
        help='For year-based retention (minutes, resolutions).',
    )
    retention_periods = fields.Integer(
        string='Retention Period (Accounting Periods)',
        tracking=True,
        help='For period-based retention (accounts, auditor reports).',
    )
    basis = fields.Selection(
        selection=[
            ('years', 'Years'),
            ('periods', 'Accounting Periods'),
        ],
        string='Basis',
        required=True,
        tracking=True,
        help='Determines which retention period field is used.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Inactive retention rules are not enforced.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )

    @api.constrains('retention_years')
    def _check_retention_years(self):
        for rec in self:
            if rec.basis == 'years' and rec.retention_years < 1:
                raise ValidationError(
                    _('Retention Period (Years) must be at least 1 for year-based retention.')
                )

    @api.constrains('retention_periods')
    def _check_retention_periods(self):
        for rec in self:
            if rec.basis == 'periods' and rec.retention_periods < 1:
                raise ValidationError(
                    _('Retention Period (Accounting Periods) must be at least 1 for period-based retention.')
                )

    def get_retention_date(self, reference_date=None):
        """Compute the retention expiry date for this rule.

        Args:
            reference_date: date or datetime to compute from (default: today)

        Returns:
            date: the date after which the document may be disposed
        """
        self.ensure_one()
        if reference_date is None:
            reference_date = date.today()
        if hasattr(reference_date, 'date'):
            reference_date = reference_date.date()

        if self.basis == 'years':
            return reference_date + relativedelta(years=self.retention_years)
        if self.basis == 'periods':
            # Approximate 1 accounting period = 1 month (12 periods = 1 year)
            return reference_date + relativedelta(months=self.retention_periods)
        return reference_date

    @api.model
    def _cron_check_disposal(self):
        """Weekly cron: flag records past retention for disposal review.

        Posts a mail.activity to the responsible user for each category
        that has records past their retention date.
        """
        today = date.today()
        retention_rules = self.search([('active', '=', True)])

        for rule in retention_rules:
            records = self._get_expired_records(rule, today)
            if not records:
                continue
            self._log_disposal_notice(rule, records, today)

    @api.model
    def _get_expired_records(self, rule, today):
        """Find records that have passed their retention date.

        Returns:
            recordset of expired records for the given rule
        """
        # 'board_reports' has no backing document model yet (only ever
        # mentioned as a retention-period category in spec, never as a
        # distinct model) -- left unmapped so it safely no-ops below
        # instead of approximating against unrelated mail.message data.
        model_map = {
            'minutes': 'govoo.minutes',
            'resolutions': 'govoo.resolution',
            'accounts': 'account.move',
            'auditor_reports': 'account.move',
        }
        model_name = model_map.get(rule.retention_category)
        if not model_name:
            return self.env['govoo.rw.retention'].browse()

        Model = self.env[model_name]
        if model_name not in self.env:
            return Model.browse()
        if not Model.browse().has_access('read'):
            return Model.browse()

        if rule.retention_category == 'minutes':
            domain = [('state', '=', 'approved')]
        elif rule.retention_category == 'resolutions':
            domain = [('state', 'in', ('passed', 'failed', 'withdrawn'))]
        else:
            domain = [('state', '=', 'posted')]
        domain.append(('company_id', '=', rule.company_id.id))

        records = Model.search(domain)
        expired = Model.browse()
        for rec in records:
            if rule.retention_category in ('accounts', 'auditor_reports'):
                reference_date = rec.invoice_date or rec.date
            else:
                reference_date = rec.create_date
            retention_date = rule.get_retention_date(reference_date)
            if retention_date <= today:
                expired |= rec
        return expired

    @api.model
    def _log_disposal_notice(self, rule, records, today):
        """Log a disposal notice for expired records.

        Creates a mail.activity on the first record for the responsible user.
        """
        if not records:
            return

        first_record = records[0]
        responsible = first_record.env.user

        # Post a message on the record
        first_record.message_post(
            body=(
                f'Document retention period expired for {len(records)} record(s) '
                f'in category "{rule.name}". Review for disposal.'
            ),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

        # Create a mail activity for review
        first_record.activity_ids.create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': f'Retention expired: {rule.name} ({len(records)} records)',
            'user_id': responsible.id,
            'date_deadline': today + relativedelta(days=7),
        })
