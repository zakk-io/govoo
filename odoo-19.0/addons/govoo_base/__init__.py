# Part of Govoo. See LICENSE file for full copyright and licensing details.

from . import models


def _hide_unused_top_level_menus(env):
    """Hide top-level app menus Kivu Capital doesn't actually use. Once a
    user holds Administrator (needed for Settings/user management), Odoo
    surfaces every installed app's menu, including several that have
    nothing to do with corporate governance -- Website, Surveys, Calendar,
    Dashboards, and the Apps/module-management screen. Hidden here rather
    than uninstalled, since other installed modules may still depend on
    them; this only affects menu visibility, nothing about the underlying
    data or model access. Each lookup tolerates the module not being
    installed at all (no hard dependency added for this), so it's a no-op
    wherever one of these happens to be absent.
    """
    menu_xmlids = [
        'website.menu_website_configuration',
        'survey.menu_surveys',
        'calendar.mail_menu_calendar',
        'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
        'base.menu_management',
    ]
    for xmlid in menu_xmlids:
        menu = env.ref(xmlid, raise_if_not_found=False)
        if menu:
            menu.active = False
