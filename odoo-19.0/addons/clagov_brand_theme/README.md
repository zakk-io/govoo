# CLAGOV Brand Theme — Odoo Community 19

Version **19.0.1.0.0** · technical name **`clagov_brand_theme`** · dependency **`web`**

An installable presentation-only add-on implementing the CLAGOV brand guide. It adds the Round Table mark, ink navigation, ivory working surfaces, white panels, champagne primary actions, Inter interface text, and Playfair Display-derived major headings to native Odoo Community screens.

## What installation applies

- **Backend, light appearance:** branded navbar, action buttons, control panels, breadcrumbs, native form inputs/sheets, lists, notebook tabs, kanban cards, menus, dialogs, notifications, chatter and calendar surfaces where those components are present.
- **Login, signup and password-reset layouts:** CLAGOV lockup, tagline, ivory page, white login card and branded controls, while preserving Odoo's authentication, OAuth, passkey, database-selection and CSRF behavior.
- **Portal, if already installed:** scoped portal surfaces and controls when Odoo's `is_portal` context is active. This module does not install Portal or Website. Ordinary public website pages are not marked for brand styling.
- **Reports:** local report fonts, an opt-in CLAGOV external layout and a non-default CLAGOV A4 paper format. Existing invoices, reports and company document layouts are not changed automatically.
- **Custom CLAGOV components:** reusable design tokens and `.clagov-heading`, `.clagov-card`, `.clagov-icon-chip` and `.clagov-premium` classes inside the branded backend/portal roots.

No governance models, menus, dashboard data, approval rules or access rules are added. The earlier concept showcase is a design reference; it is not installed as a replacement web client. Existing charts keep their native data/category palettes; the supplied chart tokens are available for your own chart components.

## Installation

This is a server add-on for Odoo **19 Community**. No Enterprise module, npm build, external font service or additional Python package is required by the add-on.

1. Extract the ZIP into a directory listed in your server's `addons_path`. The final structure must be `custom-addons/clagov_brand_theme/__manifest__.py`.
2. Make the directory readable by the Odoo service account. Add the custom-addons parent directory to `addons_path` if it is not already listed; preserve the standard Odoo addon directories.
3. Restart Odoo so it discovers the add-on and its manifest.
4. Enable developer mode, open **Apps → Update Apps List**, and update the list.
5. Remove the default **Apps** search filter, search for **CLAGOV Brand Theme**, and install it. The add-on is deliberately marked `application=False`, so it does not add a separate business application tile.
6. Reload the browser after installation. A hard refresh may be needed for previously cached assets.

For a command-line install, after adding the directory to the configured addon path and stopping the normal Odoo process for the maintenance operation:

```bash
odoo -c /etc/odoo/odoo.conf -d YOUR_DATABASE -i clagov_brand_theme --stop-after-init
```

Then restart your normal service. If your installation uses `odoo-bin`, use that executable instead. `YOUR_DATABASE` is your target database name; no database is created or selected by this package itself.

For Docker, mount the custom-addons parent at `/mnt/extra-addons` in the standard Odoo 19 image. Follow the same Apps workflow, or run the installation command using that deployment's existing configuration and database connection options.

## Upgrade and removal

After replacing this add-on's files, restart Odoo and upgrade **CLAGOV Brand Theme** in Apps, or run:

```bash
odoo -c /etc/odoo/odoo.conf -d YOUR_DATABASE -u clagov_brand_theme --stop-after-init
```

Uninstall the add-on through Apps to remove its inherited templates and declared assets. Restart Odoo and reload the browser. Company logo fields, business records, workflow states and permissions are not rewritten by installation or uninstallation. If you have integrated the optional report layout into another add-on, remove that integration/dependency before uninstalling this one.

The login layout displays CLAGOV's lockup in place of the default login logo. It does not change the stored company logo. The optional report layout retains the company's logo, address, tax information and footer alongside the CLAGOV identity.

## Optional CLAGOV report integration

In an existing custom report, use `clagov_brand_theme.external_layout` in place of `web.external_layout`. Add `clagov_brand_theme` to the custom report module's dependencies.

```xml
<template id="report_governance_record">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-set="o" t-value="doc"/>
            <t t-call="clagov_brand_theme.external_layout">
                <t t-set="layout_document_title" t-value="doc.display_name"/>
                <div class="page">
                    <h2 class="clagov-report-section">Governance record</h2>
                    <p t-field="doc.display_name"/>
                </div>
            </t>
        </t>
    </t>
</template>
```

Set the existing report action's `paperformat_id` to `clagov_brand_theme.paperformat_clagov` when using this layout, or use your own paper format with sufficient header space. The supplied A4 format has a 70 mm top margin, 58 mm header spacing and 12 mm side margins, positioning the brand lockup about 12 mm from the top in Odoo 19’s PDF renderer. Keep that spacing relationship when changing the format. It is not the database's default paper format.

Report utility classes: `.clagov-report-section`, `.clagov-report-table`, and `.clagov-number` on numeric table cells. The `o_clagov_report` scope is applied separately to header, article and footer so the PDF renderer preserves styling when it splits those sections.

## Custom CLAGOV pages

Inside native backend templates, use the optional helpers without replacing native fields or buttons:

```xml
<section class="clagov-card">
    <h2 class="clagov-heading">Board overview</h2>
    <span class="clagov-icon-chip" aria-hidden="true">
        <i class="fa fa-calendar"/>
    </span>
    <span class="clagov-premium">Premium</span>
</section>
```

The `.clagov-premium` class indicates an access/featured label. Continue using meaningful success, warning and danger colors for approval, deadline and error states.

## Design and customization

| Role | Value |
| --- | --- |
| Ink shell | `#0D141C` |
| Slate text / dark panels | `#121822` |
| Champagne primary fill | `#C8A561` |
| Ivory canvas | `#F5EFE3` |
| Ordinary text / muted text | `#151C27` / `#5B6473` |
| Decorative border / control boundary | `#E4DBC6` / `#8D8064` |
| Accessible gold text | `#80632D` |
| Control / card / panel radius | 8 / 14 / 16 px |

Edit central Sass colors in `static/src/scss/tokens.scss`. Backend compilation defaults are declared separately in `backend_variables.scss`; keep the corresponding colors in sync if you customize them. They are prepended only to backend and lazy-backend bundles, not the shared primary-variable bundle.

Odoo's generated primary/action text uses accessible dark gold, while actual primary buttons explicitly use champagne with slate labels. This keeps small primary text readable on light surfaces. Native semantic status colors and record decoration palettes are retained.

Inter is bundled at 400/500/600/700. The static Playfair Display instance at 600 has the internal family **CLAGOV Display**, respecting the upstream font's reserved-name license condition. The intended appearance remains Playfair Display. WOFF2 is used by browsers, with TTF fallback; reports declare static TTF explicitly.

Fonts are served from the add-on itself. `static/src/fonts/SOURCES.md`, the original OFL files and `SHA256SUMS` document their provenance. The SVG wordmark uses outlined glyphs and the PDF lockup uses a PNG, so logo rendering does not rely on a remotely loaded font.

## Compatibility and scope

- Target: Odoo Community **19.0**; not a package for other major versions.
- Light surfaces are scoped to `o_clagov_backend.o_clagov_light`. Odoo’s standard dark bundles exclude the light backend Sass defaults. No dark-mode switch is added. Third-party dark themes are not claimed as supported and should be tested separately.
- Optional modules are styled only when installed. The theme does not supply Enterprise components or additional business functionality.
- Another backend theme or a custom module with more specific CSS/template overrides can affect precedence. Check the combined result in your deployment.
- Portal behavior with custom Website layouts, custom reports and third-party widgets should be checked in the actual CLAGOV installation.
- This package has no Python models, controllers, JavaScript patches, post-install hooks or migrations.

See `VALIDATION.md` for the exact runtime and checks completed for this package.

## Licensing

Theme code: LGPL-3.0, included in `LICENSE`. Fonts: their included SIL Open Font License texts. CLAGOV's name and Round Table mark are brand assets reproduced from the owner's supplied reference; the code license does not grant separate trademark rights.
