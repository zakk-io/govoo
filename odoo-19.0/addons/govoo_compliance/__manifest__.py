# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Compliance',
    'summary': 'Compliance obligation catalogue, instance generation, reminders, and filing tracking',
    'description': """
Track statutory/regulatory obligations and fire reminders.
Cron-driven instance generation, staged reminders, escalation, and filing-pack export.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['govoo_base'],
    'data': [
        'security/govoo_compliance_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/govoo_compliance_obligation_views.xml',
        'views/govoo_compliance_instance_views.xml',
        'views/govoo_compliance_menus.xml',
        'report/govoo_compliance_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
