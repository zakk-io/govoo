import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Set passwords
    for uid in [5, 6, 7, 8, 9, 10, 11]:
        user = env['res.users'].browse(uid)
        if user.exists():
            user.write({'password': user.login})
            print(f"Password set for {user.login} (uid={uid})")

    # Set admin@companyb.test password
    user_b = env['res.users'].search([('login', '=', 'admin@companyb.test')])
    if user_b:
        user_b.write({'password': 'admin@companyb.test'})
        print(f"Password set for admin@companyb.test (uid={user_b.id})")

    # === COMMITTEE (id=2, check what already exists) ===
    existing_committee = env['govoo.committee'].search([('company_id', '=', 1)])
    if existing_committee:
        committee = existing_committee[0]
        print(f"Committee already exists: id={committee.id}")
    else:
        committee = env['govoo.committee'].create({
            'name': 'Board of Directors',
            'company_id': 1,
        })
        print(f"Committee created: id={committee.id}")

    # === APPOINTMENTS ===
    existing_apts = env['govoo.appointment'].search([('committee_id', '=', committee.id)])
    if not existing_apts:
        apt_director = env['govoo.appointment'].create({
            'committee_id': committee.id,
            'partner_id': 9,
            'role': 'committee_member',
            'company_id': 1,
            'date_appointed': '2025-01-01',
        })
        print(f"Director appointment: id={apt_director.id}")

        apt_secretary = env['govoo.appointment'].create({
            'committee_id': committee.id,
            'partner_id': 7,
            'role': 'secretary',
            'company_id': 1,
            'date_appointed': '2025-01-01',
        })
        print(f"Secretary appointment: id={apt_secretary.id}")
    else:
        print(f"Appointments already exist: {existing_apts.ids}")

    # === SHARE CLASS ===
    existing_class = env['govoo.share.class'].search([('company_id', '=', 1)])
    if existing_class:
        share_class = existing_class[0]
        print(f"Share class already exists: id={share_class.id}")
    else:
        share_class = env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000.0,
            'currency_id': env.ref('base.RWF').id,
            'votes_per_share': 1.0,
            'total_authorised': 1000,
            'company_id': 1,
        })
        print(f"Share class created: id={share_class.id}")

    # === ALLOTMENTS ===
    existing_allotments = env['govoo.share.allotment'].search([('share_class_id', '=', share_class.id)])
    if not existing_allotments:
        allot_shareholder = env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': 10,
            'quantity': 600,
            'price_per_share': 1000.0,
            'date_allotted': '2025-01-15',
            'certificate_no': 'SH-001',
            'company_id': 1,
        })
        allot_director = env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': 9,
            'quantity': 400,
            'price_per_share': 1000.0,
            'date_allotted': '2025-01-15',
            'certificate_no': 'SH-002',
            'company_id': 1,
        })
        print(f"Allotments created: id={allot_shareholder.id}, {allot_director.id}")
    else:
        print(f"Allotments already exist: {existing_allotments.ids}")

    # Force holding recompute
    env['govoo.share.holding'].search([('company_id', '=', 1)]).invalidate_recordset()
    holdings = env['govoo.share.holding'].search([('company_id', '=', 1)])
    for h in holdings:
        print(f"Holding: partner={h.partner_id.id}, qty={h.quantity}, pct={h.percentage}, votes={h.voting_power}")

    # === MEETING ===
    existing_meetings = env['govoo.meeting'].search([('company_id', '=', 1)])
    if not existing_meetings:
        meeting = env['govoo.meeting'].create({
            'name': 'Board Q3 Meeting',
            'committee_id': committee.id,
            'meeting_type': 'board',
            'date': '2025-09-15 10:00:00',
            'location': 'Boardroom A',
            'company_id': 1,
        })
        print(f"Meeting created: id={meeting.id}")

        # === AGENDA ITEMS ===
        item1 = env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Approve Q3 Budget',
            'sequence': 1,
            'item_type': 'decision',
            'is_confidential': False,
        })
        item2 = env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Executive Compensation Review',
            'sequence': 2,
            'item_type': 'discussion',
            'is_confidential': True,
        })
        print(f"Agenda items created: id={item1.id}, {item2.id}")

        # === RESOLUTION ===
        resolution = env['govoo.resolution'].create({
            'title': 'Approve Budget',
            'meeting_id': meeting.id,
            'resolution_type': 'ordinary',
        })
        print(f"Resolution created: id={resolution.id}")
    else:
        print(f"Meetings already exist: {existing_meetings.ids}")

    # === Company B setup ===
    company_b = env['res.company'].search([('name', '=', 'Acme Corp')])
    if company_b:
        # Verify entity type and FYE
        print(f"Company B: id={company_b.id}, entity_type={company_b.govoo_entity_type}, fye={company_b.govoo_financial_year_end}")

    cr.commit()
    print("\n=== ALL SEED DATA CREATED SUCCESSFULLY ===")
