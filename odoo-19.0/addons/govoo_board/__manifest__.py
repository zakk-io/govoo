# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Board',
    'summary': 'Board meetings, agenda, packs, minutes, resolutions, and e-voting',
    'description': """
Run board/committee/shareholder meetings end-to-end:
agenda, pack compilation, minutes, resolutions, and e-voting.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['govoo_base', 'govoo_shares', 'calendar', 'portal'],
    'data': [
        'security/govoo_board_security.xml',
        'security/ir.model.access.csv',
        'views/govoo_agenda_item_views.xml',
        'views/govoo_meeting_views.xml',
        'views/govoo_board_pack_views.xml',
        'views/govoo_minutes_views.xml',
        'views/govoo_resolution_views.xml',
        'views/govoo_vote_views.xml',
        'views/govoo_board_menus.xml',
        'report/govoo_board_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
