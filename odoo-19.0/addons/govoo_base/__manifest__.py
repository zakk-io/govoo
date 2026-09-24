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
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/govoo_base_groups.xml',
        'security/ir.model.access.csv',
        'security/govoo_base_security.xml',
        'data/ir_cron_data.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/govoo_appointment_views.xml',
        'views/govoo_committee_views.xml',
        'views/govoo_base_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
