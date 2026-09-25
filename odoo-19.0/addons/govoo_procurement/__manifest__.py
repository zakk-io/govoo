# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Procurement',
    'summary': 'Tendering via native Odoo Purchase: vendor categorization, evaluation stages, committee minutes',
    'description': """
Procurement/Tendering for Govoo (addendum module, issue #205):
vendor bids stay plain native purchase.order records (RFQ, email
invitation via action_rfq_send, and the vendor's own portal.mixin-backed
/my/purchase page with its attachment-capable chatter for bid document
uploads -- all unmodified). A thin govoo.tender case-file model adds only
what native Purchase lacks: vendor/tender categorization (reusing Contact
Tags), pre-evaluation/technical/financial evaluation stage tracking, and
committee evaluation minutes reusing govoo_board's existing meeting/minutes
lifecycle.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['govoo_base', 'govoo_board', 'purchase'],
    'data': [
        'security/govoo_procurement_security.xml',
        'security/ir.model.access.csv',
        'views/govoo_tender_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
