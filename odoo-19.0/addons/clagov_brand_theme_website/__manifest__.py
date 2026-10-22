{
    "name": "CLAGOV Brand Theme - Website Bridge",
    "summary": "CLAGOV login-page branding when the website module wraps it",
    "description": """
The `website` module (when installed) inherits web.login_layout at
priority 20 and REPLACES its entire <t t-call> subtree wholesale,
discarding clagov_brand_theme's own web.login_layout edits -- confirmed
by reading the combined/resolved arch of web.login_layout with website
installed. Rather than make the website-agnostic clagov_brand_theme
module depend on website (an optional integration, not a requirement),
this small bridge module auto-installs only when both are present and
targets website's own .oe_website_login_container wrapper directly:
the CLAGOV lockup/tagline header, and hiding the general site
header/footer chrome on the login page specifically so it renders as a
standalone branded screen rather than a full site page.
    """,
    "version": "19.0.1.0.0",
    "category": "Themes/Backend",
    "author": "Govoo",
    "license": "LGPL-3",
    "depends": ["clagov_brand_theme", "website"],
    "data": [
        "views/login_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            ("include", "clagov_brand_theme._assets_common"),
            "clagov_brand_theme_website/static/src/scss/login.scss",
        ],
    },
    "installable": True,
    "auto_install": True,
    "application": False,
}
