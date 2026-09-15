import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Check ALL obligations with full details
    obs = env['govoo.compliance.obligation'].search([])
    for ob in obs:
        print(f"ID={ob.id} | {ob.name} | active={ob.active} | entity={ob.applies_to_entity_type} | basis={ob.basis} | fixed_day={ob.fixed_day} | fixed_month={ob.fixed_month}")

    # Check company entity types
    companies = env['res.company'].search([])
    for co in companies:
        print(f"Company: {co.name} (id={co.id}) | entity_type={co.govoo_entity_type} | FYE={co.govoo_financial_year_end}")

    # Try the cron logic manually
    active_obs = env['govoo.compliance.obligation'].search([('active', '=', True)])
    print(f"\nActive obligations found: {len(active_obs)}")
    for ob in active_obs:
        print(f"  Processing: {ob.name} | entity_type={ob.applies_to_entity_type} | basis={ob.basis}")

        for company in companies:
            # Entity type check
            if ob.applies_to_entity_type != 'all':
                company_type = company.govoo_entity_type
                if company_type != ob.applies_to_entity_type:
                    print(f"    SKIP {company.name}: entity {company_type} != {ob.applies_to_entity_type}")
                    continue

            # Compute due date
            try:
                due_date = ob._get_next_due_date(company)
                print(f"    {company.name}: due_date={due_date}")
            except Exception as e:
                print(f"    {company.name}: ERROR computing due date: {e}")

    cr.commit()
