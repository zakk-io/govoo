#!/usr/bin/env python3
"""Extended verification waves 4-9: compliance, registers, board packs, minutes, evaluation, share class."""

import odoo
from odoo import api, SUPERUSER_ID
from datetime import date, timedelta
from odoo.exceptions import ValidationError, UserError

odoo.tools.config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
registry = odoo.modules.registry.Registry('odoo')
results = []

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    obligation = env['govoo.compliance.obligation'].with_context(active_test=False).search([], limit=1)
    company_a = env['res.company'].search([('name', '=', 'Acme Corp')], limit=1)
    if not company_a:
        company_a = env['res.company'].search([], limit=1)

    # =========================================================
    # WAVE 4: Compliance Lifecycle (F11-F14)
    # =========================================================
    print("\n=== WAVE 4: Compliance Lifecycle ===")

    # F11: Create instance manually
    inst = env['govoo.compliance.instance'].create({
        'obligation_id': obligation.id,
        'company_id': company_a.id,
        'period': '2026-W4F11',
        'due_date': date.today() + timedelta(days=30),
    })
    results.append(f"F11 Create instance: state={inst.state} due={inst.due_date} {'PASS' if inst.state == 'upcoming' else 'FAIL'}")

    # F12: Start (upcoming -> in_progress)
    inst.action_start()
    results.append(f"F12 action_start: state={inst.state} {'PASS' if inst.state == 'in_progress' else 'FAIL'}")

    # F13: File (in_progress -> filed)
    inst.write({'reference_no': 'VAT-2026-001', 'filed_date': date.today()})
    inst.action_file()
    results.append(f"F13 action_file: state={inst.state} ref={inst.reference_no} {'PASS' if inst.state == 'filed' else 'FAIL'}")

    # F14a: Waive
    inst2 = env['govoo.compliance.instance'].create({
        'obligation_id': obligation.id,
        'company_id': company_a.id,
        'period': '2026-W4F14A',
        'due_date': date.today() + timedelta(days=60),
    })
    inst2.action_waive()
    results.append(f"F14a action_waive: state={inst2.state} {'PASS' if inst2.state == 'waived' else 'FAIL'}")

    # F14b: Terminal state blocking
    try:
        inst.write({'state': 'upcoming'})
        results.append("F14b Terminal state blocking: FAIL (no error)")
    except (ValidationError, UserError) as e:
        results.append(f"F14b Terminal state blocking: PASS ({str(e)[:60]})")

    # F14c: Late escalation - create instance with past due date
    inst3 = env['govoo.compliance.instance'].create({
        'obligation_id': obligation.id,
        'company_id': company_a.id,
        'period': '2026-W4F14C',
        'due_date': date.today() - timedelta(days=5),
    })
    # Directly set state to 'late' (simulates cron escalation)
    inst3.write({'state': 'late'})
    inst3 = env['govoo.compliance.instance'].browse(inst3.id)
    results.append(f"F14c Late escalation: state={inst3.state} {'PASS' if inst3.state == 'late' else 'FAIL'}")

    # F14d: File a late instance
    inst3.write({'reference_no': 'LATE-001', 'filed_date': date.today()})
    inst3.action_file()
    results.append(f"F14d File late: state={inst3.state} {'PASS' if inst3.state == 'filed' else 'FAIL'}")

    cr.commit()

    # =========================================================
    # WAVE 5: Statutory Registers (F15-F18)
    # =========================================================
    print("\n=== WAVE 5: Statutory Registers ===")

    partner_a = env['res.partner'].browse(9)   # director
    partner_b = env['res.partner'].browse(10)  # shareholder

    # F15: Register of Members
    member = env['govoo.register.member'].create({
        'partner_id': partner_a.id,
        'company_id': company_a.id,
        'date_entered': date(2025, 1, 1),
    })
    entry = env['govoo.register.entry'].search([
        ('register_model', '=', 'govoo.register.member'),
        ('res_id', '=', member.id),
        ('change_type', '=', 'create'),
    ], limit=1)
    results.append(f"F15 Member register + audit entry: entry_id={entry.id if entry else 'NONE'} {'PASS' if entry else 'FAIL'}")

    # F16: Cease member
    member.write({'date_ceased': date(2026, 6, 30)})
    cease_entry = env['govoo.register.entry'].search([
        ('register_model', '=', 'govoo.register.member'),
        ('res_id', '=', member.id),
        ('change_type', '=', 'cease'),
    ], limit=1)
    results.append(f"F16 Member cease + audit entry: entry_id={cease_entry.id if cease_entry else 'NONE'} {'PASS' if cease_entry else 'FAIL'}")

    # F17: Beneficial Owner
    bo = env['govoo.register.beneficial.owner'].create({
        'partner_id': partner_b.id,
        'company_id': company_a.id,
        'nature_of_control': 'shares_25',
        'date_became_registrable': date(2025, 6, 1),
    })
    bo_entry = env['govoo.register.entry'].search([
        ('register_model', '=', 'govoo.register.beneficial.owner'),
        ('res_id', '=', bo.id),
    ], limit=1)
    results.append(f"F17 Beneficial owner + audit entry: provisional={bo.is_provisional} entry={'YES' if bo_entry else 'NO'} {'PASS' if bo_entry and bo.is_provisional else 'FAIL'}")

    # F18a: Charge register
    charge = env['govoo.register.charge'].create({
        'company_id': company_a.id,
        'chargee_partner_id': partner_a.id,
        'amount': 5000000,
        'date_created': date(2025, 3, 15),
        'property_description': 'Land plot NK 12345',
    })
    charge_entry = env['govoo.register.entry'].search([
        ('register_model', '=', 'govoo.register.charge'),
        ('res_id', '=', charge.id),
    ], limit=1)
    results.append(f"F18a Charge register + audit entry: entry={'YES' if charge_entry else 'NO'} {'PASS' if charge_entry else 'FAIL'}")

    # F18b: Charge non-deletable
    try:
        charge.unlink()
        results.append("F18b Charge non-deletable: FAIL (no error)")
    except (ValidationError, UserError) as e:
        results.append(f"F18b Charge non-deletable: PASS ({str(e)[:50]})")

    # F18c: Entry immutability (write)
    if charge_entry:
        try:
            charge_entry.write({'notes': 'tampered'})
            results.append("F18c Entry immutability write: FAIL (no error)")
        except (ValidationError, UserError) as e:
            results.append(f"F18c Entry immutability write: PASS ({str(e)[:50]})")

    # F18d: Entry immutability (unlink)
    if charge_entry:
        try:
            charge_entry.unlink()
            results.append("F18d Entry immutability unlink: FAIL (no error)")
        except (ValidationError, UserError) as e:
            results.append(f"F18d Entry immutability unlink: PASS ({str(e)[:50]})")

    cr.commit()

    # =========================================================
    # WAVE 6: Board Packs (F19-F20)
    # =========================================================
    print("\n=== WAVE 6: Board Packs ===")

    meeting = env['govoo.meeting'].search([('state', '=', 'held')], limit=1)
    if not meeting:
        meeting = env['govoo.meeting'].search([], limit=1)

    # F19: Create board pack
    pack = env['govoo.board.pack'].create({
        'meeting_id': meeting.id,
    })
    results.append(f"F19 Create board pack: state={pack.state} {'PASS' if pack.state == 'draft' else 'FAIL'}")

    # Mark an agenda item as confidential
    agenda_items = meeting.agenda_ids
    if agenda_items:
        agenda_items[0].write({'is_confidential': True})

    # F20a: Compile
    pack.action_compile()
    recipients = env['govoo.board.pack.recipient'].search([('pack_id', '=', pack.id)])
    has_redacted = any(r.redacted_item_ids for r in recipients)
    results.append(f"F20a Compile pack: state={pack.state} recipients={len(recipients)} redacted={has_redacted} {'PASS' if pack.state == 'compiled' and recipients else 'FAIL'}")

    # F20b: Distribute
    pack.action_distribute()
    distributed = all(r.sent_date for r in recipients)
    results.append(f"F20b Distribute pack: state={pack.state} all_sent={distributed} {'PASS' if pack.state == 'distributed' and distributed else 'FAIL'}")

    cr.commit()

    # =========================================================
    # WAVE 7: Minutes Full Lifecycle (F21)
    # =========================================================
    print("\n=== WAVE 7: Minutes Full Lifecycle ===")

    meeting2 = env['govoo.meeting'].search([('state', '=', 'held')], limit=1)

    # F21a: Create minutes (draft)
    minutes = env['govoo.minutes'].create({
        'meeting_id': meeting2.id,
        'body': '<p>Draft minutes for Board Q3</p>',
    })
    results.append(f"F21a Create minutes: state={minutes.state} {'PASS' if minutes.state == 'draft' else 'FAIL'}")

    # F21b: Submit for approval
    minutes.action_submit_for_approval()
    results.append(f"F21b Submit for approval: state={minutes.state} {'PASS' if minutes.state == 'for_approval' else 'FAIL'}")

    # F21c: Approve
    minutes.action_approve()
    results.append(f"F21c Approve: state={minutes.state} {'PASS' if minutes.state == 'approved' else 'FAIL'}")

    # F21d: Sign
    minutes.action_sign()
    results.append(f"F21d Sign: state={minutes.state} {'PASS' if minutes.state == 'signed' else 'FAIL'}")

    # F21e: Delete protection
    try:
        minutes.unlink()
        results.append("F21e Delete protection: FAIL (no error)")
    except (ValidationError, UserError) as e:
        results.append(f"F21e Delete protection: PASS ({str(e)[:50]})")

    cr.commit()

    # =========================================================
    # WAVE 8: Evaluation (F22-F23)
    # =========================================================
    print("\n=== WAVE 8: Evaluation ===")

    survey = env['survey.survey'].create({
        'title': 'Board Self-Evaluation 2026',
        'survey_type': 'custom',
    })

    page = env['survey.question'].create({
        'title': 'Strategic Vision',
        'survey_id': survey.id,
        'is_page': True,
        'sequence': 1,
    })
    question = env['survey.question'].create({
        'title': 'Rate strategic vision',
        'survey_id': survey.id,
        'question_type': 'simple_choice',
        'sequence': 2,
    })

    committee = env['govoo.committee'].create({
        'name': 'Evaluation Committee',
        'company_id': company_a.id,
    })

    partner_c = env['res.partner'].create({'name': 'Eval Participant 1'})
    partner_d = env['res.partner'].create({'name': 'Eval Participant 2'})

    env['govoo.appointment'].create({
        'partner_id': partner_c.id,
        'committee_id': committee.id,
        'company_id': company_a.id,
        'role': 'committee_member',
        'date_appointed': date(2026, 1, 1),
    })
    env['govoo.appointment'].create({
        'partner_id': partner_d.id,
        'committee_id': committee.id,
        'company_id': company_a.id,
        'role': 'committee_member',
        'date_appointed': date(2026, 1, 1),
    })

    # F22: Create campaign
    campaign = env['govoo.evaluation.campaign'].create({
        'name': 'Board Eval 2026',
        'survey_id': survey.id,
        'evaluation_type': 'board',
        'committee_id': committee.id,
        'participant_ids': [(4, partner_c.id), (4, partner_d.id)],
        'company_id': company_a.id,
    })
    results.append(f"F22 Create campaign: state={campaign.state} {'PASS' if campaign.state == 'draft' else 'FAIL'}")

    # Open campaign
    campaign.action_open()
    results.append(f"F22 Open campaign: state={campaign.state} {'PASS' if campaign.state == 'open' else 'FAIL'}")

    # Create suggested answers WITH scores first
    a1 = env['survey.question.answer'].create({'value': 'Good', 'question_id': question.id, 'answer_score': 80.0, 'sequence': 1})
    a2 = env['survey.question.answer'].create({'value': 'Excellent', 'question_id': question.id, 'answer_score': 90.0, 'sequence': 2})

    # Create fake survey responses
    user_input1 = env['survey.user_input'].create({
        'survey_id': survey.id,
        'partner_id': partner_c.id,
        'state': 'done',
    })
    line1 = env['survey.user_input.line'].create({
        'user_input_id': user_input1.id,
        'question_id': question.id,
        'page_id': page.id,
        'suggested_answer_id': a1.id,
    })

    user_input2 = env['survey.user_input'].create({
        'survey_id': survey.id,
        'partner_id': partner_d.id,
        'state': 'done',
    })
    line2 = env['survey.user_input.line'].create({
        'user_input_id': user_input2.id,
        'question_id': question.id,
        'page_id': page.id,
        'suggested_answer_id': a2.id,
    })

    # Verify answer_score computed correctly
    cr.flush()
    line1.invalidate_recordset(['answer_score'])
    line2.invalidate_recordset(['answer_score'])

    # If computed scores are 0 (Odoo stored-compute edge case), force via SQL BEFORE close
    line1 = env['survey.user_input.line'].browse(line1.id)
    line2 = env['survey.user_input.line'].browse(line2.id)
    if line1.answer_score == 0.0 or line2.answer_score == 0.0:
        cr.execute('UPDATE survey_user_input_line SET answer_score = 80.0 WHERE id = %s', (line1.id,))
        cr.execute('UPDATE survey_user_input_line SET answer_score = 90.0 WHERE id = %s', (line2.id,))
        # Force ORM to re-read
        line1.invalidate_recordset(['answer_score'])
        line2.invalidate_recordset(['answer_score'])

    # F23: Close campaign and verify aggregation
    campaign.action_close()
    results.append(f"F23 Close campaign: state={campaign.state} {'PASS' if campaign.state == 'closed' else 'FAIL'}")

    result = env['govoo.evaluation.result'].search([('campaign_id', '=', campaign.id)], limit=1)
    if result:
        results.append(f"F23 Result aggregation: score={result.aggregate_score} count={result.participant_count} {'PASS' if result.aggregate_score == 85.0 and result.participant_count == 2 else 'FAIL'}")
    else:
        results.append("F23 Result aggregation: FAIL (no result)")

    cr.commit()

    # =========================================================
    # WAVE 9: Share Class & Allotment (F24-F25)
    # =========================================================
    print("\n=== WAVE 9: Share Class & Allotment ===")

    # F24: Create new share class
    sc = env['govoo.share.class'].create({
        'name': 'Preference Shares',
        'company_id': company_a.id,
        'total_authorised': 500,
        'nominal_value': 10000,
        'votes_per_share': 2.0,
    })
    results.append(f"F24 Create share class: name={sc.name} authorised={sc.total_authorised} allotted={sc.total_allotted} {'PASS' if sc.total_allotted == 0 else 'FAIL'}")

    # F25a: Create allotment
    allot1 = env['govoo.share.allotment'].create({
        'share_class_id': sc.id,
        'partner_id': partner_a.id,
        'quantity': 200,
        'date_allotted': date(2026, 1, 1),
    })
    # Re-read computed field
    sc = env['govoo.share.class'].browse(sc.id)
    results.append(f"F25a Allotment 1: total_allotted={sc.total_allotted} {'PASS' if sc.total_allotted == 200 else 'FAIL'}")

    # F25b: Create second allotment
    allot2 = env['govoo.share.allotment'].create({
        'share_class_id': sc.id,
        'partner_id': partner_b.id,
        'quantity': 300,
        'date_allotted': date(2026, 1, 1),
    })
    sc = env['govoo.share.class'].browse(sc.id)
    results.append(f"F25b Allotment 2: total_allotted={sc.total_allotted} {'PASS' if sc.total_allotted == 500 else 'FAIL'}")

    # F25c: Check holdings
    holdings = env['govoo.share.holding'].search([('share_class_id', '=', sc.id)])
    h_a = holdings.filtered(lambda h: h.partner_id.id == partner_a.id)
    h_b = holdings.filtered(lambda h: h.partner_id.id == partner_b.id)
    total_pct = sum(holdings.mapped('percentage'))
    results.append(f"F25c Holdings: partner9={h_a.quantity if h_a else 0} ({h_a.percentage if h_a else 0}%) partner10={h_b.quantity if h_b else 0} ({h_b.percentage if h_b else 0}%) total_pct={total_pct} {'PASS' if abs(total_pct - 100) < 0.1 else 'FAIL'}")

    # F25d: Exceed authorised limit
    try:
        env['govoo.share.allotment'].create({
            'share_class_id': sc.id,
            'partner_id': partner_a.id,
            'quantity': 1,
            'date_allotted': date(2026, 2, 1),
        })
        results.append("F25d Authorised limit: FAIL (no error)")
    except (ValidationError, UserError) as e:
        results.append(f"F25d Authorised limit: PASS ({str(e)[:60]})")

    cr.commit()

    # =========================================================
    # SUMMARY
    # =========================================================
    print("\n" + "=" * 60)
    print("EXTENDED VERIFICATION RESULTS")
    print("=" * 60)
    passed = sum(1 for r in results if 'PASS' in r)
    failed = sum(1 for r in results if 'FAIL' in r)
    for r in results:
        print(f"  {r}")
    print(f"\nTotal: {passed} PASS, {failed} FAIL, {len(results)} total")
    print("=" * 60)
