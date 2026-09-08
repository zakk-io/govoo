# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Board Evaluation',
    'summary': 'Board and committee performance evaluations via Surveys integration',
    'description': """
Evaluation campaigns wrapping standard Odoo Surveys for board and committee
performance assessments. Confidential result aggregation with strict
individual-response confidentiality (BR-EVAL-001).
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'govoo_base',
        'survey',
    ],
    'data': [
        'security/govoo_evaluation_security.xml',
        'security/ir.model.access.csv',
        'views/govoo_evaluation_campaign_views.xml',
        'views/govoo_evaluation_result_views.xml',
        'views/govoo_evaluation_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
