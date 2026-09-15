# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Rwanda Configuration',
    'summary': 'Rwanda-specific configuration: locale, compliance obligations, and retention',
    'description': """
Provide Rwanda-specific defaults: currency (RWF), language, compliance obligation
templates, and document retention configuration.

All legal values are seeded as data records (active=False) and must never be
hard-coded in Python. Administrator must activate templates after advisor
confirmation (BR-COMP-001, BR-RW-002).
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'govoo_secretarial',
        'govoo_shares',
        'govoo_board',
        'govoo_compliance',
    ],
    'data': [
        'security/govoo_rw_security.xml',
        'security/ir.model.access.csv',
        'data/res_currency_data.xml',
        'data/govoo_compliance_obligation_data.xml',
        'data/govoo_rw_retention_data.xml',
        'data/ir_cron_data.xml',
        'views/res_config_settings_views.xml',
        'views/govoo_rw_retention_views.xml',
        'views/govoo_rw_governance_checklist_views.xml',
        'views/govoo_rw_menus.xml',
        'report/govoo_rw_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
