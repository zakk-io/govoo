# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Theme',
    'summary': 'Clagov brand: navy/gold design system for the Govoo backend and login',
    'description': """
Carries the Clagov brand identity (navy #1F3864 / gold #C6A15B) across the
whole backend and the login page via SCSS variable overrides and XML view
inheritance only -- no core template replacement, no Enterprise dependency.

Issue #250 (Epic P1 -- Brand Foundation). Final logo/wordmark/favicon/login
artwork are not yet supplied (tracked as an open item owned by Design); this
module ships the colour system and structure so those assets can be dropped
in later without further engineering work.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['web', 'govoo_base'],
    'data': [
        'views/login_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'govoo_theme/static/src/scss/variables.scss'),
        ],
        'web.assets_backend': [
            'govoo_theme/static/src/scss/backend.scss',
        ],
        'web.assets_frontend': [
            'govoo_theme/static/src/scss/login.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
