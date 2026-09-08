# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    govoo_company_number = fields.Char(
        string='Company Registration Number',
    )
    govoo_tin = fields.Char(
        string='Tax Identification Number',
    )
    govoo_incorporation_date = fields.Date(
        string='Incorporation Date',
    )
    govoo_entity_type = fields.Selection(
        selection=[
            ('private', 'Private Company'),
            ('public', 'Public Company'),
            ('llc', 'Limited Liability Company'),
            ('branch', 'Branch'),
        ],
        string='Entity Type',
        tracking=True,
    )
    govoo_registered_office_id = fields.Many2one(
        comodel_name='res.partner',
        string='Registered Office',
        # [CONFIRM] exact validation that registered office must be in Rwanda
    )
    govoo_financial_year_end = fields.Selection(
        selection=[
            ('0131', '31 January'),
            ('0228', '28 February'),
            ('0331', '31 March'),
            ('0430', '30 April'),
            ('0531', '31 May'),
            ('0630', '30 June'),
            ('0731', '31 July'),
            ('0831', '31 August'),
            ('0930', '30 September'),
            ('1031', '31 October'),
            ('1130', '30 November'),
            ('1231', '31 December'),
        ],
        string='Financial Year End',
        tracking=True,
        # [CONFIRM] whether this should be a Char or Selection
    )
