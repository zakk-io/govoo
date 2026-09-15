import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # === FIX 1: Obligation entity type mismatch ===
    # Change all 'company' obligations to 'all' since company model doesn't have 'company' value
    obs = env['govoo.compliance.obligation'].search([('applies_to_entity_type', '=', 'company')])
    for ob in obs:
        ob.write({'applies_to_entity_type': 'all'})
    print(f"Fixed {len(obs)} obligations: company -> all")

    # Re-enable the first one for testing
    if obs:
        obs[0].write({'active': True})
        print(f"Activated obligation: {obs[0].name}")

    # Trigger compliance cron
    cron = env['ir.cron'].search([('cron_name', '=', 'Compliance: Generate Instances')])
    cron.method_direct_trigger()
    print("Cron triggered")

    # Check instances
    instances = env['govoo.compliance.instance'].search([])
    for inst in instances:
        print(f"Instance: obligation={inst.obligation_id.name}, company={inst.company_id.name}, state={inst.state}, due={inst.due_date}, period={inst.period}")
    if not instances:
        print("No instances generated")

    # === FIX 2: Test holdings recompute after transfer ===
    # The transfer (id=1) was registered. Let's manually trigger recompute
    holdings = env['govoo.share.holding'].search([('share_class_id', '=', 3)])
    print(f"\nBefore recompute:")
    for h in holdings:
        print(f"  Partner {h.partner_id.id}: qty={h.quantity}, pct={h.percentage}, votes={h.voting_power}")

    # Manually trigger recomputation
    env['govoo.share.holding']._recompute_holdings(3)

    # Refresh from DB
    holdings.invalidate_recordset()
    holdings = env['govoo.share.holding'].search([('share_class_id', '=', 3)])
    print(f"\nAfter recompute:")
    for h in holdings:
        print(f"  Partner {h.partner_id.id}: qty={h.quantity}, pct={h.percentage}, votes={h.voting_power}")

    # Verify the fix
    expected = {9: 500, 10: 500}  # After 100-share transfer from 10→9
    all_ok = True
    for h in holdings:
        if h.quantity != expected.get(h.partner_id.id, 0):
            print(f"  BUG: Partner {h.partner_id.id} expected qty={expected.get(h.partner_id.id)}, got {h.quantity}")
            all_ok = False
    if all_ok:
        print("\n  Holdings recompute FIXED!")

    cr.commit()
