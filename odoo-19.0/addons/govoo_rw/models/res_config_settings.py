# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    govoo_default_language = fields.Selection(
        selection=[
            ('en_US', 'English'),
            ('rw_RW', 'Kinyarwanda'),
            ('fr_FR', 'French'),
        ],
        string='Default Language',
        config_parameter='govoo.default_language',
        default='en_US',
    )
    govoo_default_timezone = fields.Selection(
        selection=[
            ('Africa/Kigali', 'Africa/Kigali'),
        ],
        string='Default Timezone',
        config_parameter='govoo.default_timezone',
        default='Africa/Kigali',
    )
    govoo_default_date_format = fields.Selection(
        selection=[
            ('DD/MM/YYYY', 'DD/MM/YYYY'),
            ('MM/DD/YYYY', 'MM/DD/YYYY'),
            ('YYYY-MM-DD', 'YYYY-MM-DD'),
        ],
        string='Default Date Format',
        config_parameter='govoo.default_date_format',
        default='DD/MM/YYYY',
    )

    # Selection value -> Odoo strftime date_format
    _DATE_FORMAT_MAP = {
        'DD/MM/YYYY': '%d/%m/%Y',
        'MM/DD/YYYY': '%m/%d/%Y',
        'YYYY-MM-DD': '%Y-%m-%d',
    }

    def set_values(self):
        super().set_values()
        # Apply locale settings to the company's partner record when
        # saved. res.company itself has no lang/tz field (both are on
        # res.partner/res.users) -- writing them to company directly
        # crashed unconditionally before this fix; tracked separately
        # as #136, fixed here since it blocked testing this setting at
        # all.
        company = self.env.company
        lang = self.govoo_default_language or 'en_US'
        company.partner_id.write({
            'lang': lang,
            'tz': self.govoo_default_timezone or 'Africa/Kigali',
        })

        # Apply the date format to the selected language's res.lang record.
        # res.lang.date_format is the only mechanism Odoo actually uses to
        # render dates -- there is no per-company date-format setting, so
        # this is the only way to make this setting do anything. Note this
        # changes date rendering for every company using that language on
        # this instance, not just the current one (res.lang is
        # instance-global). If the language isn't installed, there's no
        # res.lang record to update -- skip silently rather than error.
        strftime_format = self._DATE_FORMAT_MAP.get(self.govoo_default_date_format)
        if strftime_format:
            res_lang = self.env['res.lang'].search([('code', '=', lang)], limit=1)
            if res_lang:
                res_lang.date_format = strftime_format
