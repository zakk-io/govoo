import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Verify
    active_obs = env['govoo.compliance.obligation'].search([('active', '=', True)])
    print(f"Active obligations: {len(active_obs)}")
    for ob in active_obs:
        print(f"  {ob.name} | entity={ob.applies_to_entity_type} | basis={ob.basis} | fixed_day={ob.fixed_day} | fixed_month={ob.fixed_month}")

    # Trigger cron
    cron = env['ir.cron'].search([('cron_name', '=', 'Compliance: Generate Instances')])
    cron.method_direct_trigger()
    print("Cron triggered")

    # Check instances
    instances = env['govoo.compliance.instance'].search([])
    print(f"Instances: {len(instances)}")
    for inst in instances:
        print(f"  {inst.obligation_id.name} | {inst.company_id.name} | {inst.state} | due={inst.due_date} | period={inst.period}")

    cr.commit()
