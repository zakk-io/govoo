# CLAGOV Brand Theme validation

Version: **19.0.1.0.0** · verified **22 October 2026**.

## Runtime used

- Official `odoo:19.0` Community image: `Odoo Server 19.0-20260810`.
- PostgreSQL 16 in a separate disposable database.
- `wkhtmltopdf 0.12.6.1 (with patched qt)` from that image.
- Native `web`, `contacts` and `portal` modules. The theme itself depends only on `web`.
- Template and asset hooks also reviewed against official Odoo 19.0 source commit `e5a4af13360c0fb54ea5ae3301804cccb09668cd`.

Testing used local containers and synthetic records. It did not change the owner's deployed Odoo system.

## Completed checks

| Check | Result |
| --- | --- |
| Initial install with Community Web and no Enterprise dependency | Passed |
| Upgrade after final manifest and report-template changes | Passed |
| Python source syntax, manifest paths, XML parsing, font checksums | Passed |
| Backend OWL extension loaded without replacing native navigation | Passed |
| Login, authentication and backend loading | Passed |
| Contacts list, company form, create/save, tabs, chatter and contact dialog | Passed |
| Native Contacts kanban | Passed |
| Optional Portal `/my`, conditional scope, local font and white entry cards | Passed |
| Optional two-page A4 PDF, repeated header/table heading and page counters | Passed |
| Fonts embedded in the generated PDF | Passed |
| Standard company report layout remains outside the CLAGOV report scope | Passed |
| CLAGOV paper format is not a database default | Passed |
| ZIP integrity and single addon root | Passed |

Actual Odoo asset compilation produced no CSS errors:

| Bundle | Compiled CSS bytes |
| --- | ---: |
| `web.assets_web` | 969,268 |
| `web.assets_backend_lazy` | 7,924 |
| `web.assets_web_dark` | 983,520 |
| `web.assets_backend_lazy_dark` | 7,856 |
| `web.assets_frontend` | 484,624 |
| `web.report_assets_common` | 400,357 |

Dark-bundle compilation was checked separately to confirm exclusion of the light backend Sass defaults. It is not a claim of compatibility with third-party dark themes.

The PDF exercise used 40 synthetic table rows across two pages and the documented optional external layout, including a company logo, multi-line address, tax identifier, tagline and footer. The supplied A4 format reserves 70 mm above the content and keeps the header origin at 12 mm. `CLAGOV Display`, `Inter Medium`, `Inter SemiBold` and `Inter Bold` were embedded. Header spacing was verified against the actual renderer so the lockup and company header remain above content on continuation pages.

## Installed-interface previews

These are captures of native Odoo 19 screens with this module installed, rather than the earlier concept visualization:

- [Login](docs/login-preview.png)
- [Contacts list](docs/list-preview.png)
- [Company form](docs/form-preview.png)
- [Contacts kanban](docs/kanban-preview.png)
- [Portal](docs/portal-preview.png)
- [PDF page 1](docs/report-page-1.png), [PDF page 2](docs/report-page-2.png)

## Deployment-specific checks

The package does not include business applications or governance workflows. Custom CLAGOV views, third-party themes/widgets, unusual company report headers, RTL layouts and mobile browsers were not exercised in the owner's deployment. Check those combinations there. Optional modules receive styles when present; they are not installed by the theme. Existing reports use their current layouts until their report module explicitly opts in as described in `README.md`.

No validation fixture, test password, local server URL or disposable database is shipped as addon configuration.
