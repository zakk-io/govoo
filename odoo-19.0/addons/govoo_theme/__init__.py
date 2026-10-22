# Part of Govoo. See LICENSE file for full copyright and licensing details.

from . import models


def _fix_color_scheme_default_to_light(env):
    """One-time migration for users created before this module's
    color_scheme default changed from "System" to "Light" (see
    models/res_users_settings.py for why). Only touches rows still on
    "system" -- a user who explicitly chose Dark keeps that choice."""
    settings = env['res.users.settings'].sudo().search([('color_scheme', '=', 'system')])
    settings.write({'color_scheme': 'light'})
