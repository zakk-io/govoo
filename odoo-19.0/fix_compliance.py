import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Fix My Company entity type to match obligations
    company = env['res.company'].browse(1)
    company.write({'govoo_entity_type': 'company'})
    print(f"My Company entity_type updated to: {company.govoo_entity_type}")

    # Trigger compliance cron
    cr.execute("SELECT ir_cron_direct_trigger FROM ir_cron WHERE cron_name = 'Compliance: Generate Instances'")
    # Use method direct trigger instead
    env['ir.cron'].browse(27).method_direct_trigger()
    print("Cron triggered")

    # Check instances
    instances = env['govoo.compliance.instance'].search([])
    for inst in instances:
        print(f"Instance: obligation={inst.obligation_id.name}, company={inst.company_id.name}, state={inst.state}, due={inst.due_date}, period={inst.period}")

    if not instances:
        print("No instances generated - checking cron logs...")

    cr.commit()
