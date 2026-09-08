# Part of Govoo. See LICENSE file for full copyright and licensing details.

import calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooComplianceObligation(models.Model):
    _name = 'govoo.compliance.obligation'
    _description = 'Compliance Obligation (Catalogue)'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(
        string='Obligation Name',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    authority = fields.Char(
        string='Authority',
        tracking=True,
        help='Regulatory authority (e.g. RRA, RDB).',
    )
    frequency = fields.Selection(
        selection=[
            ('annual', 'Annual'),
            ('quarterly', 'Quarterly'),
            ('monthly', 'Monthly'),
            ('event', 'Event-Driven'),
        ],
        string='Frequency',
        required=True,
        tracking=True,
    )
    basis = fields.Selection(
        selection=[
            ('fixed_date', 'Fixed Date'),
            ('fye_relative', 'Financial Year End Relative'),
            ('event_relative', 'Event-Driven'),
        ],
        string='Due Date Basis',
        required=True,
        tracking=True,
    )
    fixed_day = fields.Integer(
        string='Fixed Day',
        help='Day of month for fixed_date basis.',
    )
    fixed_month = fields.Integer(
        string='Fixed Month',
        help='Month (1-12) for fixed_date basis.',
    )
    fye_offset_months = fields.Integer(
        string='FYE Offset (Months)',
        help='Months after financial year end for fye_relative basis.',
    )
    lead_time_days = fields.Integer(
        string='Lead Time (Days)',
        default=0,
        tracking=True,
    )
    applies_to_entity_type = fields.Selection(
        selection=[
            ('all', 'All Entity Types'),
            ('company', 'Company'),
            ('npo', 'NPO'),
            ('private', 'Private'),
            ('public', 'Public'),
            ('llc', 'LLC'),
            ('branch', 'Branch'),
        ],
        string='Applies To',
        default='all',
        required=True,
        help='Entity types this obligation applies to. "All" applies to every entity type.',
        tracking=True,
    )
    active = fields.Boolean(
        string='Active',
        default=False,
        tracking=True,
        help='Seeded templates default to False until advisor confirmation (BR-COMP-001).',
    )
    instance_ids = fields.One2many(
        comodel_name='govoo.compliance.instance',
        inverse_name='obligation_id',
        string='Instances',
    )

    @api.constrains('lead_time_days')
    def _check_lead_time_days(self):
        for rec in self:
            if rec.lead_time_days < 0:
                raise ValidationError(_('Lead Time must be zero or positive.'))

    @api.constrains('fixed_day', 'fixed_month')
    def _check_fixed_date_fields(self):
        for rec in self:
            if rec.basis == 'fixed_date':
                if rec.fixed_day < 1 or rec.fixed_day > 31:
                    raise ValidationError(_('Fixed Day must be between 1 and 31.'))
                if rec.fixed_month < 1 or rec.fixed_month > 12:
                    raise ValidationError(_('Fixed Month must be between 1 and 12.'))

    def _get_next_due_date(self, company, reference_date=None):
        """Compute the next due date for this obligation given a company.

        Args:
            company: res.company record
            reference_date: date to compute from (default: today)

        Returns:
            date or None if cannot compute (e.g. missing FYE config)
        """
        if reference_date is None:
            reference_date = date.today()

        if self.basis == 'fixed_date':
            return self._compute_fixed_date(reference_date)
        if self.basis == 'fye_relative':
            return self._compute_fye_relative(company, reference_date)
        if self.basis == 'event_relative':
            # Event-relative obligations are triggered manually, not by cron
            return None
        return None

    def _compute_fixed_date(self, reference_date):
        """Compute next due date for fixed_date basis."""
        year = reference_date.year
        due = date(year, self.fixed_month, self.fixed_day)
        if due <= reference_date:
            year += 1
            due = date(year, self.fixed_month, self.fixed_day)
        return due

    def _compute_fye_relative(self, company, reference_date):
        """Compute next due date for fye_relative basis.

        Requires company.govoo_financial_year_end to be set.
        Returns None if not set (fail closed).
        """
        fye = company.govoo_financial_year_end
        if not fye:
            return None

        # Parse month/day from selection value (e.g. "0630" -> month=6, day=30)
        month = int(fye[:2])
        day = int(fye[2:])
        year = reference_date.year
        fye_date = date(year, month, day)

        # Apply offset
        offset_months = self.fye_offset_months or 0
        target_month = fye_date.month + offset_months
        target_year = fye_date.year
        while target_month > 12:
            target_month -= 12
            target_year += 1
        # Handle day overflow (e.g. Jan 31 + 1 month -> Feb 28)
        last_day = calendar.monthrange(target_year, target_month)[1]
        target_day = min(day, last_day)
        due = date(target_year, target_month, target_day)

        if due <= reference_date:
            # Try next year
            target_year += 1
            fye_next = date(target_year, month, day)
            target_month = fye_next.month + offset_months
            target_year = fye_next.year
            while target_month > 12:
                target_month -= 12
                target_year += 1
            last_day = calendar.monthrange(target_year, target_month)[1]
            target_day = min(day, last_day)
            due = date(target_year, target_month, target_day)

        return due
