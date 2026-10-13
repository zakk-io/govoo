# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooVoteProxyTC(GovooBoardTestBase):
    """Issue #269 item 1: proxy voting appointments."""

    def test_proxy_can_cast_vote_for_principal(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.env['govoo.vote.proxy'].create({
            'meeting_id': meeting.id,
            'principal_partner_id': self.partner_a.id,
            'proxy_partner_id': self.partner_b.id,
        })

        vote = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'cast_by_id': self.partner_b.id,
            'choice': 'for',
        })
        self.assertEqual(vote.voter_id, self.partner_a)
        self.assertEqual(vote.cast_by_id, self.partner_b)
        self.assertEqual(vote.weight, 1.0)

    def test_is_active_proxy_for_true_for_appointed_proxy(self):
        meeting = self._make_meeting()
        self.env['govoo.vote.proxy'].create({
            'meeting_id': meeting.id,
            'principal_partner_id': self.partner_a.id,
            'proxy_partner_id': self.partner_b.id,
        })
        self.assertTrue(
            self.env['govoo.vote.proxy']._is_active_proxy_for(
                self.partner_b.id, self.partner_a.id, meeting.id,
            )
        )

    def test_is_active_proxy_for_false_for_unrelated_partner(self):
        meeting = self._make_meeting()
        self.env['govoo.vote.proxy'].create({
            'meeting_id': meeting.id,
            'principal_partner_id': self.partner_a.id,
            'proxy_partner_id': self.partner_b.id,
        })
        self.assertFalse(
            self.env['govoo.vote.proxy']._is_active_proxy_for(
                self.partner_c.id, self.partner_a.id, meeting.id,
            )
        )

    def test_proxy_scoped_to_one_meeting_does_not_leak_to_another(self):
        meeting_1 = self._make_meeting()
        meeting_2 = self._make_meeting()
        self.env['govoo.vote.proxy'].create({
            'meeting_id': meeting_1.id,
            'principal_partner_id': self.partner_a.id,
            'proxy_partner_id': self.partner_b.id,
        })
        self.assertTrue(
            self.env['govoo.vote.proxy']._is_active_proxy_for(
                self.partner_b.id, self.partner_a.id, meeting_1.id,
            )
        )
        self.assertFalse(
            self.env['govoo.vote.proxy']._is_active_proxy_for(
                self.partner_b.id, self.partner_a.id, meeting_2.id,
            )
        )

    def test_inactive_proxy_is_not_an_active_proxy(self):
        meeting = self._make_meeting()
        proxy = self.env['govoo.vote.proxy'].create({
            'meeting_id': meeting.id,
            'principal_partner_id': self.partner_a.id,
            'proxy_partner_id': self.partner_b.id,
        })
        proxy.active = False
        self.assertFalse(
            self.env['govoo.vote.proxy']._is_active_proxy_for(
                self.partner_b.id, self.partner_a.id, meeting.id,
            )
        )

    def test_self_proxy_rejected(self):
        meeting = self._make_meeting()
        with self.assertRaises(ValidationError):
            self.env['govoo.vote.proxy'].create({
                'meeting_id': meeting.id,
                'principal_partner_id': self.partner_a.id,
                'proxy_partner_id': self.partner_a.id,
            })

    def test_duplicate_proxy_per_meeting_rejected(self):
        meeting = self._make_meeting()
        self.env['govoo.vote.proxy'].create({
            'meeting_id': meeting.id,
            'principal_partner_id': self.partner_a.id,
            'proxy_partner_id': self.partner_b.id,
        })
        with self.assertRaises(Exception):
            self.env['govoo.vote.proxy'].create({
                'meeting_id': meeting.id,
                'principal_partner_id': self.partner_a.id,
                'proxy_partner_id': self.partner_c.id,
            })

    def test_get_active_proxies_for(self):
        meeting = self._make_meeting()
        self.env['govoo.vote.proxy'].create({
            'meeting_id': meeting.id,
            'principal_partner_id': self.partner_a.id,
            'proxy_partner_id': self.partner_b.id,
        })
        proxies = self.env['govoo.vote.proxy']._get_active_proxies_for(self.partner_b.id)
        self.assertEqual(len(proxies), 1)
        self.assertEqual(proxies.principal_partner_id, self.partner_a)
