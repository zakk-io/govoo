import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Fix ALL obligations: change 'company' to 'all' (since company model doesn't have 'company' value)
    obs = env['govoo.compliance.obligation'].search([('applies_to_entity_type', '=', 'company')])
    for ob in obs:
        ob.write({'applies_to_entity_type': 'all'})
    print(f"Fixed {len(obs)} obligations: company -> all")

    # Activate VAT Return for testing
    vat = env['govoo.compliance.obligation'].search([('name', '=', 'VAT Return (Monthly)')], limit=1)
    if vat:
        vat.write({'active': True})
        print(f"Activated: {vat.name}")

    # Verify
    active_obs = env['govoo.compliance.obligation'].search([('active', '=', True)])
    print(f"Active obligations: {len(active_obs)}")
    for ob in active_obs:
        print(f"  {ob.name} | entity={ob.applies_to_entity_type} | basis={ob.basis} | fixed_day={ob.fixed_day} | fixed_month={ob.fixed_month}")

    # Trigger cron
    cron = env['ir.cron'].search([('cron_name', '=', 'Compliance: Generate Instances')])
    cron.method_direct_trigger()
    print("\nCron triggered")

    # Check instances
    instances = env['govoo.compliance.instance'].search([])
    print(f"Instances: {len(instances)}")
    for inst in instances:
        print(f"  {inst.obligation_id.name} | {inst.company_id.name} | {inst.state} | due={inst.due_date} | period={inst.period}")

    cr.commit()
    print("\nCommitted")
