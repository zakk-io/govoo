# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'

    # zxs_entp_theme (the Enterprise Home Menu add-on) defaults every new
    # user to "System", which silently follows the browser's OS dark-mode
    # preference. None of Govoo's brand theme modules ship a dark-mode
    # variant, so landing in dark mode makes the brand disappear in
    # favour of zxs's own dark Enterprise palette, and several existing
    # govoo_* widgets (kpi_strip, action_items_dashboard) hardcode a
    # light background with no dark-mode counterpart -- together that
    # produces mismatched light-on-dark cards. Pin new users to Light
    # until a real dark variant exists; _fix_color_scheme_default_to_light
    # in __init__.py handles the same thing for users created before
    # this change.
    color_scheme = fields.Selection(default='light')
