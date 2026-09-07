"""
Automated Test Suite for Stage 3: Human-in-the-Loop (HITL) Transfer Harness.
Verifies:
1. initiate_transfer raises confirmation without debiting balance.
2. confirm_transfer executes debit only upon explicit human approval.
3. confirm_transfer cancels transfer cleanly upon user rejection.
4. Prevention of double-spend / replay on already processed confirmation IDs.
5. Integration with Stage 2 policy validation harness.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.transfer_service import transfer_service
from src.bank_db import bank_db
from src.bank_tools import initiate_transfer, confirm_transfer


class TestHITLTransferHarness(unittest.TestCase):

    def setUp(self):
        # Reset database and pending transfer store before each test
        bank_db.reset()
        transfer_service.pending_transfers.clear()

    def test_initiate_transfer_does_not_debit_balance(self):
        """Step 1: initiate_transfer creates pending request, does NOT debit funds."""
        initial_balance = bank_db.get_account("ACC1001")["balance"]

        result = initiate_transfer(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=3000.0,
            remarks="Gift",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "PENDING_CONFIRMATION")
        self.assertTrue(result["confirmation_id"].startswith("CONF-"))
        self.assertTrue(result["human_in_the_loop"]["requires_user_confirmation"])
        self.assertIn("Please confirm", result["human_in_the_loop"]["prompt"])

        # Crucial HITL verification: Balance MUST NOT change yet
        balance_after_initiate = bank_db.get_account("ACC1001")["balance"]
        self.assertEqual(balance_after_initiate, initial_balance)

    def test_confirm_transfer_executes_debit(self):
        """Step 2: confirm_transfer with 'confirm' debits funds and completes transfer."""
        initial_source = bank_db.get_account("ACC1001")["balance"]
        initial_dest = bank_db.get_account("ACC2002")["balance"]  # Sneha Rao

        # 1. Initiate
        init_res = initiate_transfer(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=2500.0,
            remarks="Project payment",
        )
        conf_id = init_res["confirmation_id"]

        # 2. Confirm
        confirm_res = confirm_transfer(confirmation_id=conf_id, action="confirm")

        self.assertTrue(confirm_res["success"])
        self.assertEqual(confirm_res["status"], "COMPLETED")
        self.assertTrue(confirm_res["transaction_id"].startswith("TXN"))
        self.assertEqual(confirm_res["remaining_balance"], initial_source - 2500.0)

        # Verify DB balances updated
        self.assertEqual(bank_db.get_account("ACC1001")["balance"], initial_source - 2500.0)
        self.assertEqual(bank_db.get_account("ACC2002")["balance"], initial_dest + 2500.0)

    def test_confirm_transfer_cancel_aborts_cleanly(self):
        """Step 2: confirm_transfer with 'cancel' discards transfer without moving money."""
        initial_balance = bank_db.get_account("ACC1001")["balance"]

        # 1. Initiate
        init_res = initiate_transfer(
            source_account_id="ACC1001",
            recipient="Amit Patel",
            amount=4000.0,
            remarks="Rent split",
        )
        conf_id = init_res["confirmation_id"]

        # 2. User cancels
        cancel_res = confirm_transfer(confirmation_id=conf_id, action="cancel")

        self.assertTrue(cancel_res["success"])
        self.assertEqual(cancel_res["status"], "CANCELLED")
        self.assertIn("CANCELLED by user", cancel_res["message"])

        # Verify balance untouched
        self.assertEqual(bank_db.get_account("ACC1001")["balance"], initial_balance)

    def test_replay_prevention_on_already_processed_confirmation(self):
        """Safety: Attempting to confirm an already processed transfer must be blocked."""
        init_res = initiate_transfer(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=1000.0,
        )
        conf_id = init_res["confirmation_id"]

        # First confirmation succeeds
        first_res = confirm_transfer(confirmation_id=conf_id, action="confirm")
        self.assertTrue(first_res["success"])

        # Second confirmation on same ID must fail
        second_res = confirm_transfer(confirmation_id=conf_id, action="confirm")
        self.assertFalse(second_res["success"])
        self.assertEqual(second_res["status"], "ALREADY_PROCESSED")

    def test_invalid_confirmation_id(self):
        """Safety: Non-existent confirmation ID is rejected."""
        res = confirm_transfer(confirmation_id="CONF-DOESNOTEXIST", action="confirm")
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "INVALID_CONFIRMATION_ID")

    def test_policy_violation_blocks_initiation(self):
        """Integration: Stage 2 policy violations block transfer initiation immediately."""
        # 1. Exceeds daily limit (₹50,000)
        limit_res = initiate_transfer(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=60000.0,
        )
        self.assertFalse(limit_res["success"])
        self.assertEqual(limit_res["status"], "POLICY_REJECTED")
        self.assertEqual(limit_res["policy_code"], "DAILY_LIMIT_EXCEEDED")

        # 2. Ambiguous recipient (matches > 1)
        ambig_res = initiate_transfer(
            source_account_id="ACC1001",
            recipient="Rahul",
            amount=1000.0,
        )
        self.assertFalse(ambig_res["success"])
        self.assertTrue(ambig_res["requires_verification"])
        self.assertEqual(ambig_res["policy_code"], "AMBIGUOUS_MATCH")

        # 3. Non-existent recipient
        unreg_res = initiate_transfer(
            source_account_id="ACC1001",
            recipient="Unknown Person",
            amount=500.0,
        )
        self.assertFalse(unreg_res["success"])
        self.assertEqual(unreg_res["policy_code"], "NO_MATCH")


if __name__ == "__main__":
    print("=" * 65)
    print(" 🤝  Running Stage 3 Human-in-the-Loop (HITL) Test Suite  🤝 ")
    print("=" * 65)
    unittest.main(verbosity=2)
