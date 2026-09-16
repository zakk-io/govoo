# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Portal & Dashboard',
    'summary': 'Director/Shareholder self-service portal and internal dashboard views',
    'description': """
Portal controllers and templates for Director and Shareholder self-service access,
plus personalized internal dashboard aggregation views for the Govoo backend.

No new transactional models — this is purely a presentation layer over data
owned by other Govoo modules.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'govoo_base',
        'govoo_secretarial',
        'govoo_shares',
        'govoo_board',
        'govoo_compliance',
        'govoo_rw',
        'govoo_evaluation',
        'portal',
        'website',
        'board',
    ],
    'data': [
        'views/portal_templates.xml',
        'views/govoo_portal_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
