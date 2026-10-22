# Part of Govoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Govoo Theme',
    'summary': 'Clagov brand: navy/gold design system for the Govoo backend and public site',
    'description': """
Carries the Clagov brand identity (navy #1F3864 / gold #C6A15B) across the
whole backend and the login page via SCSS variable overrides and XML view
inheritance only -- no core template replacement.

Issue #250 (Epic P1 -- Brand Foundation). Final logo/wordmark/favicon/login
artwork are not yet supplied (tracked as an open item owned by Design); this
module ships the colour system and structure so those assets can be dropped
in later without further engineering work.

Depends on zxs_entp_theme (issue #359) purely for asset load ordering: this
module's variables.scss must compile before zxs_entp_theme's own, so the
Clagov colours (set without !default) win over zxs's own Enterprise purple
defaults (set with !default). No code from this module calls into
zxs_entp_theme; it only needs to load after it.

Also pins every user's colour scheme to Light instead of zxs's own
"System" default, which silently follows the browser's OS dark-mode
preference -- this module has no dark-mode SCSS of its own yet, so
landing in dark mode made the Clagov brand look like it had vanished.
    """,
    'author': 'Govoo',
    'category': 'Governance',
    'version': '19.0.1.0.4',
    'license': 'LGPL-3',
    'depends': ['web', 'govoo_base', 'zxs_entp_theme'],
    'data': [
        'views/login_templates.xml',
    ],
    'post_init_hook': '_fix_color_scheme_default_to_light',
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'govoo_theme/static/src/scss/variables.scss'),
        ],
        'web.assets_backend': [
            'govoo_theme/static/src/scss/backend.scss',
        ],
        'web.assets_frontend': [
            'govoo_theme/static/src/scss/frontend.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
