import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # === Committees ===
    committee = env['govoo.committee'].create({
        'name': 'Board of Directors',
        'company_id': 1,
    })
    print(f"Committee: {committee.id} - {committee.name}")

    # === Appointments ===
    director_partner = env['res.partner'].browse(9)
    secretary_partner = env['res.partner'].browse(7)

    apt_director = env['govoo.appointment'].create({
        'partner_id': director_partner.id,
        'committee_id': committee.id,
        'role': 'chair',
        'date_appointed': '2026-01-01',
        'company_id': 1,
    })
    print(f"Appointment director: {apt_director.id}")

    apt_secretary = env['govoo.appointment'].create({
        'partner_id': secretary_partner.id,
        'role': 'secretary',
        'date_appointed': '2026-01-01',
        'company_id': 1,
    })
    print(f"Appointment secretary: {apt_secretary.id}")

    # === Share Class ===
    share_class = env['govoo.share.class'].create({
        'name': 'Ordinary Shares',
        'nominal_value': 1000,
        'votes_per_share': 1.0,
        'total_authorised': 1000,
        'company_id': 1,
    })
    print(f"Share class: {share_class.id} - {share_class.name}")

    # === Allotments ===
    shareholder_partner = env['res.partner'].browse(10)

    allotment_shareholder = env['govoo.share.allotment'].create({
        'share_class_id': share_class.id,
        'partner_id': shareholder_partner.id,
        'quantity': 600,
        'date_allotted': '2026-01-15',
        'company_id': 1,
    })
    print(f"Allotment shareholder: {allotment_shareholder.id} - qty=600")

    allotment_director = env['govoo.share.allotment'].create({
        'share_class_id': share_class.id,
        'partner_id': director_partner.id,
        'quantity': 400,
        'date_allotted': '2026-01-15',
        'company_id': 1,
    })
    print(f"Allotment director: {allotment_director.id} - qty=400")

    # === Verify Holdings ===
    holdings = env['govoo.share.holding'].search([('share_class_id', '=', share_class.id)])
    for h in holdings:
        print(f"Holding: partner={h.partner_id.id}, qty={h.quantity}, pct={h.percentage}, votes={h.voting_power}")

    # === Meeting ===
    meeting = env['govoo.meeting'].create({
        'name': 'Board Q3 Meeting',
        'meeting_type': 'board',
        'committee_id': committee.id,
        'date': '2026-10-15 10:00:00',
        'quorum_required': 2,
        'company_id': 1,
    })
    print(f"Meeting: {meeting.id} - {meeting.name}")

    # === Agenda Items ===
    agenda1 = env['govoo.agenda.item'].create({
        'meeting_id': meeting.id,
        'title': 'Approval of Previous Minutes',
        'item_type': 'noting',
        'sequence': 1,
    })
    agenda2 = env['govoo.agenda.item'].create({
        'meeting_id': meeting.id,
        'title': 'Budget Review',
        'item_type': 'decision',
        'sequence': 2,
    })
    agenda3 = env['govoo.agenda.item'].create({
        'meeting_id': meeting.id,
        'title': 'Confidential Strategy Discussion',
        'item_type': 'discussion',
        'sequence': 3,
        'is_confidential': True,
    })
    print(f"Agenda items: {agenda1.id}, {agenda2.id}, {agenda3.id}")

    # === Resolution ===
    resolution = env['govoo.resolution'].create({
        'title': 'Approve Budget',
        'resolution_type': 'ordinary',
        'meeting_id': meeting.id,
        'company_id': 1,
    })
    print(f"Resolution: {resolution.id} - {resolution.title}")

    # === Compliance: activate one obligation ===
    env['govoo.compliance.obligation'].search([]).write({'active': False})
    vat = env['govoo.compliance.obligation'].search([('name', '=', 'VAT Return (Monthly)')], limit=1)
    if vat:
        vat.write({'active': True})
        print(f"Activated obligation: {vat.name}")

    # === Share Transfer (draft) ===
    transfer = env['govoo.share.transfer'].create({
        'share_class_id': share_class.id,
        'transferor_id': shareholder_partner.id,
        'transferee_id': director_partner.id,
        'quantity': 100,
        'company_id': 1,
    })
    print(f"Transfer: {transfer.id} - draft state")

    cr.commit()
    print("\n=== Seed data created successfully ===")
