{
    "name": "CLAGOV Brand Theme",
    "summary": "CLAGOV branding for Odoo 19 Community: backend, login, portal and report layout",
    "description": "CLAGOV's ink, champagne and ivory identity applied to native Odoo 19 Community screens. Includes local fonts, login and portal styling, and an optional report layout. Presentation only; no business models or Enterprise dependencies.",
    "version": "19.0.1.0.0",
    "category": "Themes/Backend",
    "author": "CLAGOV",
    "website": "https://clagov.com",
    "license": "LGPL-3",
    # zxs_entp_theme (Enterprise Home Menu) is not a hard requirement of
    # this theme's own features, but it also prepends colour variables
    # into web.assets_backend/web._assets_primary_variables (all guarded
    # with !default, same as this module's own backend_variables.scss).
    # Depending on it guarantees this module's SCSS compiles after zxs's,
    # so CLAGOV's colours win deterministically instead of depending on
    # whichever unrelated module happens to load first -- the same
    # OR-combination-style ordering fragility already documented in this
    # project's own govoo_contracts_security.xml (issue #352) and the
    # earlier govoo_theme/zxs_entp_theme dependency fix (issue #359).
    "depends": ["web", "zxs_entp_theme"],
    "data": [
        "views/webclient_templates.xml",
        "views/report_templates.xml",
    ],
    "assets": {
        "clagov_brand_theme._assets_common": [
            "clagov_brand_theme/static/src/scss/fonts.scss",
            "clagov_brand_theme/static/src/scss/tokens.scss",
            # Liquid Glass delta (themes/clagov theme/CLAGOV-Liquid-Glass-Only):
            # material mixins only, emits no CSS by itself -- must be
            # available before lg_opt_in.scss in every bundle that uses it.
            "clagov_brand_theme/static/src/scss/lg_materials.scss",
        ],
        "web.assets_backend": [
            ("prepend", "clagov_brand_theme/static/src/scss/backend_variables.scss"),
            ("include", "clagov_brand_theme._assets_common"),
            # Loads before backend.scss so backend.scss's own regression
            # fixes (Home Menu background, navbar, etc.) keep cascade
            # precedence over the opt-in glass classes where they collide.
            "clagov_brand_theme/static/src/scss/lg_opt_in.scss",
            # App-wide glass on every native business view (.o_view_controller),
            # extending the opt-in delta beyond login/Home Menu -- see the
            # file's own header comment for why this is safe to apply broadly.
            "clagov_brand_theme/static/src/scss/glass_workspace.scss",
            "clagov_brand_theme/static/src/scss/backend.scss",
            "clagov_brand_theme/static/src/xml/navbar.xml",
            "clagov_brand_theme/static/src/xml/home_menu.xml",
        ],
        "web.assets_backend_lazy": [
            ("prepend", "clagov_brand_theme/static/src/scss/backend_variables.scss"),
        ],
        "web.assets_web_dark": [
            ("remove", "clagov_brand_theme/static/src/scss/backend_variables.scss"),
        ],
        "web.assets_backend_lazy_dark": [
            ("remove", "clagov_brand_theme/static/src/scss/backend_variables.scss"),
        ],
        "web.assets_frontend": [
            ("prepend", "clagov_brand_theme/static/src/scss/frontend_variables.scss"),
            ("include", "clagov_brand_theme._assets_common"),
            "clagov_brand_theme/static/src/scss/frontend.scss",
            # clagov_brand_theme_website's own login.scss (a downstream
            # module, depends=clagov_brand_theme) always loads after this
            # module's own web.assets_frontend contributions, so placing
            # lg_opt_in.scss here is still "before the final regression-fix
            # stylesheet" for the login page specifically.
            "clagov_brand_theme/static/src/scss/lg_opt_in.scss",
        ],
        "web.report_assets_common": [
            "clagov_brand_theme/static/src/scss/report_fonts.scss",
            "clagov_brand_theme/static/src/scss/tokens.scss",
            "clagov_brand_theme/static/src/scss/reports.scss",
        ],
    },
    "images": ["static/description/icon.png"],
    "application": False,
    "auto_install": False,
    "installable": True,
}
