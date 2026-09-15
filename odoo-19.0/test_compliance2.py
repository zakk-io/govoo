import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Check current obligation state
    obs = env['govoo.compliance.obligation'].search([])
    for ob in obs:
        print(f"Obligation: {ob.name}, active={ob.active}, entity={ob.applies_to_entity_type}, basis={ob.basis}")

    # Check if any are active
    active_obs = env['govoo.compliance.obligation'].search([('active', '=', True)])
    print(f"\nActive obligations: {len(active_obs)}")

    if not active_obs:
        print("No active obligations. Activating VAT Return...")
        vat = env['govoo.compliance.obligation'].search([('name', '=', 'VAT Return (Monthly)')], limit=1)
        if vat:
            vat.write({'active': True})
            print(f"Activated: {vat.name}, entity_type={vat.applies_to_entity_type}")

    # Trigger cron
    cron = env['ir.cron'].search([('cron_name', '=', 'Compliance: Generate Instances')])
    cron.method_direct_trigger()
    print("Cron triggered")

    # Check instances
    instances = env['govoo.compliance.instance'].search([])
    print(f"\nInstances: {len(instances)}")
    for inst in instances:
        print(f"  {inst.obligation_id.name} | {inst.company_id.name} | {inst.state} | due={inst.due_date} | period={inst.period}")

    cr.commit()
