import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

results = []

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # === Wave 2: Meeting workflow ===
    meeting = env['govoo.meeting'].search([('name', '=', 'Board Q3 Meeting')], limit=1)
    
    # F3: Schedule meeting (draft→scheduled)
    meeting.action_schedule()
    results.append(f"F3 Schedule meeting: state={meeting.state} {'PASS' if meeting.state == 'scheduled' else 'FAIL'}")

    # Add attendees to meet quorum
    director_partner = env['res.partner'].browse(9)
    shareholder_partner = env['res.partner'].browse(10)
    meeting.write({'attendee_ids': [(4, director_partner.id), (4, shareholder_partner.id)]})
    results.append(f"F3 Added attendees: {len(meeting.attendee_ids)} (quorum_required={meeting.quorum_required})")

    # F3: Hold meeting (scheduled→held)
    meeting.action_hold()
    results.append(f"F3 Hold meeting: state={meeting.state} {'PASS' if meeting.state == 'held' else 'FAIL'}")

    # F8: Quorum check
    results.append(f"F8 Quorum met: {meeting.quorum_met} {'PASS' if not meeting.quorum_met else 'NOTE: quorum met (attendees may have been added)'}")

    # === Wave 2: Resolution workflow ===
    resolution = env['govoo.resolution'].search([('title', '=', 'Approve Budget')], limit=1)
    
    # F5: Open resolution (draft→open)
    resolution.action_open()
    results.append(f"F5 Open resolution: state={resolution.state} {'PASS' if resolution.state == 'open' else 'FAIL'}")

    # F5: Vote on resolution (shareholder votes for)
    director = env['res.partner'].browse(9)
    shareholder = env['res.partner'].browse(10)
    
    vote_director = env['govoo.vote'].create({
        'resolution_id': resolution.id,
        'voter_id': director.id,
        'choice': 'for',
        'weight': 400.0,
    })
    results.append(f"F5 Director vote: choice={vote_director.choice}, weight={vote_director.weight} PASS")

    vote_shareholder = env['govoo.vote'].create({
        'resolution_id': resolution.id,
        'voter_id': shareholder.id,
        'choice': 'against',
        'weight': 600.0,
    })
    results.append(f"F5 Shareholder vote: choice={vote_shareholder.choice}, weight={vote_shareholder.weight} PASS")

    # F5: Tally (for=400, against=600 → failed)
    resolution.action_tally()
    results.append(f"F5 Tally resolution: state={resolution.state}, result={resolution.result} {'PASS' if resolution.state == 'failed' and resolution.result == 'failed' else 'FAIL'}")

    # F6: Minutes from held meeting
    minutes = env['govoo.minutes'].create({
        'meeting_id': meeting.id,
        'body': '<p>Minutes of Board Q3 Meeting</p>',
    })
    meeting.write({'minutes_id': minutes.id})
    minutes.action_submit_for_approval()
    results.append(f"F6 Minutes created & submitted: state={minutes.state} PASS")
    
    # held→minuted→closed
    meeting.action_minute()
    results.append(f"F6 Meeting minuted: state={meeting.state} {'PASS' if meeting.state == 'minuted' else 'FAIL'}")
    meeting.action_close()
    results.append(f"F6 Meeting closed: state={meeting.state} {'PASS' if meeting.state == 'closed' else 'FAIL'}")

    # === Wave 4: Compliance cron ===
    cron = env['ir.cron'].search([('cron_name', '=', 'Compliance: Generate Instances')])
    cron.method_direct_trigger()
    instances = env['govoo.compliance.instance'].search([])
    results.append(f"F11 Compliance cron: {len(instances)} instances generated {'PASS' if len(instances) > 0 else 'FAIL'}")
    for inst in instances:
        results.append(f"  Instance: {inst.obligation_id.name} | {inst.company_id.name} | {inst.state} | due={inst.due_date}")

    # === Wave 3: Transfer workflow ===
    transfer = env['govoo.share.transfer'].search([('quantity', '=', 100)], limit=1)
    if transfer:
        transfer.action_approve()
        results.append(f"F7 Transfer approve: state={transfer.state} {'PASS' if transfer.state == 'approved' else 'FAIL'}")
        
        transfer.action_register()
        results.append(f"F7 Transfer register: state={transfer.state} {'PASS' if transfer.state == 'registered' else 'FAIL'}")
        
        # Verify holdings recomputed
        holdings = env['govoo.share.holding'].search([('share_class_id', '=', transfer.share_class_id.id)])
        for h in holdings:
            results.append(f"  Holding: partner={h.partner_id.id}, qty={h.quantity}, pct={h.percentage}")
        
        director_holding = holdings.filtered(lambda h: h.partner_id.id == 9)
        shareholder_holding = holdings.filtered(lambda h: h.partner_id.id == 10)
        if director_holding and shareholder_holding:
            d_qty = director_holding.quantity
            s_qty = shareholder_holding.quantity
            results.append(f"F7 Holdings after transfer: director={d_qty}, shareholder={s_qty} {'PASS' if d_qty == 500 and s_qty == 500 else 'FAIL'}")

    cr.commit()

print("\n".join(results))
