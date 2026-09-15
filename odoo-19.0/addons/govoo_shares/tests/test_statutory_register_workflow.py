# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class TestStatutoryRegisterWorkflow(GovooShareTestBase):
    """TC-WF-SEC-001: appointment created -> resigned; holding created ->
    reduced to zero. Register of Directors and Register of Members both
    reflect ceased status; ledger entries recorded for both.

    Placed in govoo_shares's suite (not govoo_secretarial's) since it
    needs govoo.share.holding, which govoo_secretarial doesn't depend on;
    govoo_shares depends on govoo_secretarial, so everything needed is
    available here.
    """

    def test_director_resignation_reflected_on_register(self):
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        register = self.env['govoo.register.director'].search([
            ('appointment_id', '=', appointment.id),
        ], limit=1)
        self.assertTrue(register, 'Register of Directors entry should be created.')
        self.assertFalse(register.date_resigned)

        appointment.write({'date_resigned': '2026-06-01'})
        self.assertEqual(register.date_resigned, appointment.date_resigned)
        self.assertEqual(register.state, appointment.state)

        entries = self.env['govoo.register.entry'].search([
            ('register_model', '=', 'govoo.register.director'),
            ('res_id', '=', register.id),
            ('change_type', '=', 'cease'),
        ])
        self.assertTrue(entries, 'A "cease" ledger entry should be recorded.')

    def test_holding_reduced_to_zero_reflected_on_register(self):
        allotment = self._make_allotment(self.partner_a, 10)
        member = self.env['govoo.register.member'].search([
            ('partner_id', '=', self.partner_a.id),
            ('company_id', '=', self.company.id),
        ], limit=1)
        self.assertTrue(member, 'Register of Members entry should be created.')
        self.assertFalse(member.date_ceased)

        # Transfer the entire holding away -- quantity drops to zero
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': allotment.quantity,
            'date_transferred': '2026-03-01',
        })
        transfer.action_approve()
        transfer.action_register()

        member.invalidate_recordset(['date_ceased'])
        self.assertTrue(member.date_ceased, 'Register of Members should reflect ceased status.')

        entries = self.env['govoo.register.entry'].search([
            ('register_model', '=', 'govoo.register.member'),
            ('res_id', '=', member.id),
            ('change_type', '=', 'cease'),
        ])
        self.assertTrue(entries, 'A "cease" ledger entry should be recorded.')
