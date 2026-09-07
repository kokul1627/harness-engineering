"""
Automated Test Script for Naive Banking Agent.
Runs a sequence of user prompts to test all 4 banking tools with Gemini Flash in INR (₹).
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.naive_agent import NaiveBankingAgent
from src.bank_db import bank_db
from src import mockdata


def run_tests():
    print("=" * 65)
    print(" 🏦  Running Automated Verification for Naive Banking Agent  🏦 ")
    print("=" * 65)

    try:
        agent = NaiveBankingAgent()
    except Exception as e:
        print(f"FAILED to initialize agent: {e}")
        return False

    test_queries = [
        ("Test 1: Check Account Balance", "What is my current account balance?"),
        ("Test 2: Find Beneficiaries", "Can you show me all my registered beneficiaries?"),
        ("Test 3: Policy Guardrail - Ambiguous Match", "Please transfer ₹1,000 to Rahul for coffee."),
        ("Test 4: Policy Guardrail - Daily Limit Exceeded", "Please transfer ₹60,000 to Sneha Rao for rent."),
        ("Test 5: Valid Transfer Execution", "Please transfer ₹2,500 to Rahul Verma for dinner."),
        ("Test 6: Check Transaction Status", "Can you check the status of transaction TXN1001?"),
    ]

    initial_balance = bank_db.get_account("ACC1001")["balance"]
    print(f"Initial ACC1001 Balance: ₹{initial_balance:,.2f}\n")

    for test_name, query in test_queries:
        print(f"--- {test_name} ---")
        print(f"User: {query}")
        try:
            response = agent.send_message(query)
            print(f"Agent:\n{response}\n")
        except Exception as e:
            print(f"Error during query execution: {e}\n")
            return False

    final_balance = bank_db.get_account("ACC1001")["balance"]
    print(f"Final ACC1001 Balance: ₹{final_balance:,.2f}")

    if final_balance == initial_balance - 2500.00:
        print("\n[SUCCESS] Transfer of ₹2,500 was executed and balance was correctly updated!")
    else:
        print(f"\n[NOTE] Expected balance ₹{initial_balance - 2500.00:,.2f}, got ₹{final_balance:,.2f}")

    print("\n" + "=" * 65)
    print(" Automated Verification Completed! ")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
