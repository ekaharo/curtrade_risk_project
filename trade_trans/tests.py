from django.test import TestCase
from django.contrib.auth.models import User

from .models import TradeRqst

class TradeRqstTests(TestCase):
    @classmethod

    def setUpTestData(cls):
        # Create a user
        testuser1 = User.objects.create_user(
            username = 'testuser1', password='abcd1234567'
        )
        testuser1.save()

        # Create a TradeRQST

        test_create_traderqst = TradeRqst.objects.create(
            requestor = testuser1,
            rqst_rcpt_id = 9876,
            rcvd_signal_type = 'EURCAD',
            wlr = 95,
            rcvd_entry_point = 50,
            rcvd_tp = 60,
            rcdv_sl = 45,
            rcvd_asset = 'HeHee'
        )

        test_create_traderqst.save()

    def test_create_traderqst(self):
        """Test a logged in user 
        can create a trade rqst succesfully"""
        trade_rqst = TradeRqst.objects.get(id=1)
        expected_requestor = f"{trade_rqst.requestor}"
        expected_rqst_rcpt_id = trade_rqst.rqst_rcpt_id
        expected_rcvd_signal_type = trade_rqst.rcvd_signal_type
        expected_wlr = trade_rqst.wlr
        expected_rcvd_entry_point = trade_rqst.rcvd_entry_point
        expected_rcvd_tp = trade_rqst.rcvd_tp
        expected_rcdv_sl = trade_rqst.rcdv_sl
        expected_rcvd_asset = trade_rqst.rcvd_asset

        self.assertEqual(expected_requestor, 'testuser1')
        self.assertEqual(expected_rqst_rcpt_id, 9876)
        self.assertEqual(expected_rcvd_signal_type, 'EURCAD')
        self.assertEqual(expected_wlr, 95)
        self.assertEqual(expected_rcvd_entry_point, 50)
        self.assertEqual(expected_rcvd_tp, 60)
        self.assertEqual(expected_rcdv_sl, 45)
        self.assertEqual(expected_rcvd_asset, 'HeHee')