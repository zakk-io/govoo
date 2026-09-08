# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Secretarial',
    'summary': 'Statutory registers and append-only audit ledger',
    'description': """
Register of directors, register of members, beneficial ownership register,
register of charges, and append-only audit ledger.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['govoo_base'],
    'data': [
        'security/govoo_secretarial_security.xml',
        'security/ir.model.access.csv',
        'views/govoo_register_director_views.xml',
        'views/govoo_register_member_views.xml',
        'views/govoo_register_beneficial_owner_views.xml',
        'views/govoo_register_charge_views.xml',
        'views/govoo_register_entry_views.xml',
        'views/govoo_secretarial_menus.xml',
        'report/govoo_register_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
