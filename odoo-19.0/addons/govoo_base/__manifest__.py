# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Base',
    'summary': 'Foundation module for corporate governance in Rwanda',
    'description': """
Shared security groups, res.partner/res.company governance extensions,
appointment (role-over-time) and committee models.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.4',
    'license': 'LGPL-3',
    # zxs_entp_theme is what actually defines res.users.settings.color_scheme
    # (its own field, with the selection values) -- models/res_users_settings.py
    # below only extends it (default='light', no selection=). Without this
    # dependency Odoo's module graph has no reason to load zxs_entp_theme
    # before govoo_base, and when it doesn't, that extension crashes with
    # "Field res.users.settings.color_scheme without selection" (hit on a
    # from-scratch install where there's no prior accidental load order to
    # mask it). Never rely on implicit install order for a field extension.
    'depends': ['base', 'mail', 'contacts', 'zxs_entp_theme'],
    'data': [
        'security/govoo_base_groups.xml',
        'security/ir.model.access.csv',
        'security/govoo_base_security.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/govoo_appointment_views.xml',
        'views/govoo_committee_views.xml',
        'views/govoo_base_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'govoo_base/static/src/scss/ribbon.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_post_init',
}
