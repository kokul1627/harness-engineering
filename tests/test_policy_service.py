"""
Unit and Integration Tests for Stage 2 Policy Service & Guardrail Harness.
Validates all policy constraints specified by the user:
1. If no match -> no transfer
2. If matches > 1 -> ask for verification / confirm user
3. amount > 0
4. account status = active
5. amount <= account balance
6. account transfer < daily limit
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

from services.policy_service import (
    evaluate_transfer_policy,
    resolve_beneficiary,
    check_transfer_limits_and_status,
)
from src.bank_db import bank_db
from src.bank_tools import transfer_money
from src import mockdata


class TestPolicyService(unittest.TestCase):

    def setUp(self):
        # Reset mock database before each test
        bank_db.reset()

    def test_policy_amount_positive(self):
        """Policy: amount > 0 must be strictly positive."""
        decision_zero = evaluate_transfer_policy(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=0.0,
        )
        self.assertFalse(decision_zero.is_allowed)
        self.assertEqual(decision_zero.policy_code, "INVALID_AMOUNT")

        decision_negative = evaluate_transfer_policy(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=-200.0,
        )
        self.assertFalse(decision_negative.is_allowed)
        self.assertEqual(decision_negative.policy_code, "INVALID_AMOUNT")

    def test_policy_no_match_no_transfer(self):
        """Policy: if no matches -> no transfer."""
        decision = evaluate_transfer_policy(
            source_account_id="ACC1001",
            recipient="Unknown Person",
            amount=500.0,
        )
        self.assertFalse(decision.is_allowed)
        self.assertEqual(decision.policy_code, "NO_MATCH")
        self.assertFalse(decision.requires_confirmation)
        self.assertIn("No registered beneficiary matches", decision.message)

    def test_policy_multiple_matches_requires_confirmation(self):
        """Policy: if matches > 1 -> ask for verification and confirm user."""
        decision = evaluate_transfer_policy(
            source_account_id="ACC1001",
            recipient="Rahul",
            amount=1500.0,
        )
        self.assertFalse(decision.is_allowed)
        self.assertTrue(decision.requires_confirmation)
        self.assertEqual(decision.policy_code, "AMBIGUOUS_MATCH")
        self.assertGreaterEqual(len(decision.candidate_beneficiaries), 2)
        candidate_names = [c["name"] for c in decision.candidate_beneficiaries]
        self.assertIn("Rahul Verma", candidate_names)
        self.assertIn("Rahul Sharma", candidate_names)
        self.assertIn("Verification required", decision.message)

    def test_policy_account_status_active(self):
        """Policy: account status = active (inactive/frozen accounts denied)."""
        # ACC9001 is set to status 'FROZEN' in mockdata
        decision = evaluate_transfer_policy(
            source_account_id="ACC9001",
            recipient="ACC2001",
            amount=500.0,
        )
        self.assertFalse(decision.is_allowed)
        self.assertEqual(decision.policy_code, "INACTIVE_ACCOUNT")
        self.assertIn("FROZEN", decision.message)

    def test_policy_amount_exceeds_balance(self):
        """Policy: amount <= account balance."""
        # ACC1001 initial balance is ₹75,000
        decision = evaluate_transfer_policy(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=80000.0,
        )
        self.assertFalse(decision.is_allowed)
        self.assertEqual(decision.policy_code, "INSUFFICIENT_FUNDS")
        self.assertIn("Insufficient funds", decision.message)

    def test_policy_daily_limit(self):
        """Policy: account transfer < daily limit (cumulative daily transfers)."""
        # ACC1001 daily limit is ₹50,000
        decision = evaluate_transfer_policy(
            source_account_id="ACC1001",
            recipient="Sneha Rao",
            amount=50001.0,
        )
        self.assertFalse(decision.is_allowed)
        self.assertEqual(decision.policy_code, "DAILY_LIMIT_EXCEEDED")
        self.assertIn("Daily transfer limit exceeded", decision.message)

    def test_policy_successful_single_match_transfer(self):
        """Policy: when all policies pass and matches == 1 -> transfer approved."""
        initial_balance = bank_db.get_account("ACC1001")["balance"]

        # Tool execution with policy harness
        result = transfer_money(
            source_account_id="ACC1001",
            destination_account_id="",
            recipient="Sneha Rao",
            amount=2000.0,
            remarks="Project share",
        )
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("status"), "COMPLETED")
        self.assertEqual(result.get("policy_check"), "PASSED")

        new_balance = bank_db.get_account("ACC1001")["balance"]
        self.assertEqual(new_balance, initial_balance - 2000.0)

    def test_policy_confirmation_resolution(self):
        """Policy: user confirms specific account after ambiguous match -> executes."""
        initial_balance = bank_db.get_account("ACC1001")["balance"]

        # Step 1: Query with 'Rahul' triggers confirmation
        step1 = transfer_money(
            source_account_id="ACC1001",
            recipient="Rahul",
            amount=1200.0,
        )
        self.assertFalse(step1.get("success"))
        self.assertTrue(step1.get("requires_confirmation"))

        # Step 2: User provides confirmed account 'ACC2004' (Rahul Sharma)
        step2 = transfer_money(
            source_account_id="ACC1001",
            recipient="Rahul",
            amount=1200.0,
            confirmed_account_id="ACC2004",
            remarks="Confirmed transfer to Rahul Sharma",
        )
        self.assertTrue(step2.get("success"))
        self.assertEqual(step2.get("destination_account_id"), "ACC2004")
        self.assertEqual(step2.get("status"), "COMPLETED")

        new_balance = bank_db.get_account("ACC1001")["balance"]
        self.assertEqual(new_balance, initial_balance - 1200.0)


if __name__ == "__main__":
    print("=" * 65)
    print(" 🛡️  Running Stage 2 Policy Service & Guardrail Test Suite  🛡️ ")
    print("=" * 65)
    unittest.main(verbosity=2)
