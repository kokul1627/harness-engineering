"""
Banking Tools for Gemini Function Calling.
These functions interface with the policy harness and mock bank database.
"""

from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from .bank_db import bank_db
    from . import mockdata
except ImportError:
    from bank_db import bank_db
    import mockdata



def get_balance(account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict[str, Any]:
    """
    Retrieve the current account balance and status for a specific bank account.

    Args:
        account_id: The unique identifier of the bank account (defaults to 'ACC1001').

    Returns:
        A dictionary containing the balance, currency (INR), currency_symbol (₹), owner name, and status.
    """
    return bank_db.get_balance(account_id)


def find_beneficiaries(account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict[str, Any]:
    """
    Find and list registered beneficiaries for a specific bank account.
    Beneficiaries can be used as destination accounts for fund transfers.

    Args:
        account_id: The unique identifier of the bank account (defaults to 'ACC1001').

    Returns:
        A dictionary containing the list of registered beneficiaries (name, nickname, account_id, bank_name, ifsc_code).
    """
    return bank_db.find_beneficiaries(account_id)


def get_beneficiaries(account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict[str, Any]:
    """Alias for find_beneficiaries."""
    return find_beneficiaries(account_id)


def transfer_money(
    source_account_id: str = mockdata.DEFAULT_USER_ACCOUNT,
    destination_account_id: str = "",
    recipient: str = "",
    amount: float = 0.0,
    remarks: str = "",
    confirmed_account_id: str = "",
) -> Dict[str, Any]:
    """
    Execute a money transfer after verifying banking policy constraints and safety harness.

    Harness Policies Enforced:
    1. Beneficiary Matching:
       - No match -> Transfer rejected.
       - Multiple matches (>1) -> Verification / user confirmation required.
       - Exactly 1 match -> Resolved.
    2. amount > 0 (Must be positive).
    3. account_status == 'ACTIVE' (Sender account must be active).
    4. amount <= account_balance (Sufficient funds).
    5. amount + transferred_today <= daily_limit (Must not exceed daily transfer limit).

    Args:
        source_account_id: The sender's account identifier (defaults to 'ACC1001').
        destination_account_id: The recipient's account ID or identifier.
        recipient: The recipient's name or nickname if account ID is not known.
        amount: The monetary amount in INR (₹) to transfer (must be > 0).
        remarks: Optional description or note for the transfer (e.g., 'dinner', 'rent').
        confirmed_account_id: Specific account ID provided by user after confirmation.

    Returns:
        A dictionary with transaction result or policy denial explanation.
    """
    # Use destination_account_id or recipient name for resolution
    target_query = destination_account_id or recipient
    confirmation_acc = confirmed_account_id or (destination_account_id if destination_account_id.startswith("ACC") else "")

    # Run Stage 2 Policy Guardrail Harness
    from services.policy_service import evaluate_transfer_policy

    decision = evaluate_transfer_policy(
        source_account_id=source_account_id,
        recipient=target_query,
        amount=amount,
        confirmed_account_id=confirmation_acc if confirmation_acc else None,
    )

    if not decision.is_allowed:
        return {
            "success": False,
            "policy_code": decision.policy_code,
            "requires_confirmation": decision.requires_confirmation,
            "message": decision.message,
            "candidate_beneficiaries": decision.candidate_beneficiaries,
        }

    # If policy harness passed, execute transfer on bank state
    resolved_destination = decision.resolved_account_id or destination_account_id
    transfer_result = bank_db.transfer_money(
        source_account_id=source_account_id,
        destination_account_id=resolved_destination,
        amount=amount,
        remarks=remarks,
    )
    transfer_result["policy_check"] = "PASSED"
    return transfer_result


def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
    """
    Check the current status and details of a previous transaction by its transaction ID.

    Args:
        transaction_id: The unique transaction identifier (e.g., 'TXN1001', 'TXN1002', 'TXN1003').

    Returns:
        A dictionary containing status ('COMPLETED', 'PENDING', 'FAILED'), amount in ₹, source, destination, and timestamp.
    """
    return bank_db.get_transaction_status(transaction_id)


# List of tool functions exposed to the Gemini model
BANKING_TOOLS = [
    get_balance,
    find_beneficiaries,
    transfer_money,
    get_transaction_status,
]
