# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Contracts',
    'summary': 'Contract register, approval routing, e-signature, and obligation tracking',
    'description': """
Contract Management for Govoo (addendum module):
contract register, template/clause library, approval routing linked to board
approval and delegation-of-authority, related-party conflict checks,
e-signature execution, obligation/milestone tracking, and renewal/termination.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['govoo_base', 'govoo_compliance', 'govoo_board', 'portal'],
    'data': [
        'security/govoo_contracts_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/govoo_contract_type_views.xml',
        'views/govoo_contract_delegation_views.xml',
        'views/govoo_contract_views.xml',
        'views/govoo_contracts_menus.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
