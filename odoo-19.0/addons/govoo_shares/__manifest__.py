# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Shares',
    'summary': 'Cap table, share classes, allotments, transfers, and computed holdings',
    'description': """
Share classes, allotments, transfers, and computed holdings.
Feeds the Register of Members and shareholder vote weighting.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['govoo_secretarial'],
    'data': [
        'security/govoo_shares_security.xml',
        'security/ir.model.access.csv',
        'views/govoo_share_class_views.xml',
        'views/govoo_share_allotment_views.xml',
        'views/govoo_share_transfer_views.xml',
        'views/govoo_share_holding_views.xml',
        'views/govoo_register_member_views.xml',
        'views/govoo_shares_menus.xml',
        'report/govoo_shares_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
