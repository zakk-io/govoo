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

    def set_values(self):
        super().set_values()
        # Apply locale settings to the company when saved
        company = self.env.company
        lang = self.govoo_default_language or 'en_US'
        company.write({
            'lang': lang,
            'tz': self.govoo_default_timezone or 'Africa/Kigali',
        })
