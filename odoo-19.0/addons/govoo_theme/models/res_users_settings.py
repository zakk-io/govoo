# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'

    # zxs_entp_theme defaults every new user to "System", which silently
    # follows the browser's OS dark-mode preference. govoo_theme has no
    # dark-mode SCSS of its own yet (the Clagov brand only covers the
    # light bundle), so landing in dark mode makes the Clagov navy/gold
    # navbar disappear in favour of zxs's own dark Enterprise palette,
    # and several existing govoo_* widgets (kpi_strip,
    # action_items_dashboard) hardcode a light background with no
    # dark-mode counterpart -- together that produces mismatched
    # light-on-dark cards. Pin new users to Light until a real Clagov
    # dark variant exists; _fix_color_scheme_default_to_light in
    # __init__.py handles the same thing for users created before this
    # change.
    color_scheme = fields.Selection(default='light')
