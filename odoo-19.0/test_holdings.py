import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Verify transfer exists
    transfer = env['govoo.share.transfer'].browse(1)
    print(f"Transfer: {transfer.state}, qty={transfer.quantity}, from={transfer.transferor_id.id}, to={transfer.transferee_id.id}")

    # Verify allotments
    allotments = env['govoo.share.allotment'].search([('share_class_id', '=', 3)])
    for a in allotments:
        print(f"Allotment: partner={a.partner_id.id}, qty={a.quantity}")

    # Call recompute
    print("\nCalling _recompute_holdings(3)...")
    env['govoo.share.holding']._recompute_holdings(3)

    # Check results
    holdings = env['govoo.share.holding'].search([('share_class_id', '=', 3)])
    for h in holdings:
        print(f"Holding: partner={h.partner_id.id}, qty={h.quantity}, pct={h.percentage}, votes={h.voting_power}")

    cr.commit()
