"""
Banking Tools for Gemini Function Calling.
Stage 1: Basic banking tools
Stage 2: Policy & Guardrail Harness
Stage 3: Human-in-the-Loop (HITL) Transfer Harness
Stage 4: Observability & Monitoring Trace Harness
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

from services.observability_service import observability


def get_balance(account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict[str, Any]:
    """
    Retrieve current account balance, status, and daily transfer limits.

    Args:
        account_id: The unique identifier of the bank account (defaults to 'ACC1001').

    Returns:
        A dictionary containing the balance, currency (INR), currency_symbol (₹), owner name, status, daily limit, and remaining allowance.
    """
    return observability.trace_tool_execution(
        tool_name="get_balance",
        arguments={"account_id": account_id},
        execution_func=lambda: bank_db.get_balance(account_id),
    )


def find_beneficiaries(account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict[str, Any]:
    """
    Find and list registered beneficiaries for a specific bank account.
    Beneficiaries can be used as destination accounts for fund transfers.

    Args:
        account_id: The unique identifier of the bank account (defaults to 'ACC1001').

    Returns:
        A dictionary containing the list of registered beneficiaries (name, nickname, account_id, bank_name, ifsc_code).
    """
    return observability.trace_tool_execution(
        tool_name="find_beneficiaries",
        arguments={"account_id": account_id},
        execution_func=lambda: bank_db.find_beneficiaries(account_id),
    )


def get_beneficiaries(account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict[str, Any]:
    """Alias for find_beneficiaries."""
    return find_beneficiaries(account_id)


def initiate_transfer(
    source_account_id: str = mockdata.DEFAULT_USER_ACCOUNT,
    recipient: str = "",
    destination_account_id: str = "",
    amount: float = 0.0,
    remarks: str = "",
    confirmed_account_id: str = "",
) -> Dict[str, Any]:
    """
    Step 1 of Transfer (Human-in-the-Loop): Initiate a money transfer and raise human confirmation.
    
    Validates Stage 2 banking policies (registered beneficiary, positive amount, active account, sufficient balance, daily limit).
    If valid, generates a unique Confirmation ID and prepares a pending transfer request.
    Does NOT debit or transfer any money until confirm_transfer is called.

    Args:
        source_account_id: The sender's account identifier (defaults to 'ACC1001').
        recipient: The recipient's name, nickname, or account ID.
        destination_account_id: Optional destination account ID if known.
        amount: The monetary amount in INR (₹) to transfer (must be > 0).
        remarks: Optional description or note for the transfer.
        confirmed_account_id: Specific account ID provided by user if multiple matches existed.

    Returns:
        A dictionary containing confirmation_id, recipient details, formatted amount, and the confirmation prompt to present to the user.
    """
    from services.transfer_service import transfer_service

    args = {
        "source_account_id": source_account_id,
        "recipient": recipient or destination_account_id,
        "destination_account_id": destination_account_id,
        "amount": amount,
        "remarks": remarks,
        "confirmed_account_id": confirmed_account_id,
    }

    return observability.trace_tool_execution(
        tool_name="initiate_transfer",
        arguments=args,
        execution_func=lambda: transfer_service.initiate_transfer(**args),
    )


def confirm_transfer(
    confirmation_id: str,
    action: str = "confirm",
) -> Dict[str, Any]:
    """
    Step 2 of Transfer (Human-in-the-Loop): Finalize or cancel an initiated transfer upon human confirmation.

    Args:
        confirmation_id: The unique confirmation ID returned by initiate_transfer (e.g. 'CONF-A1B2C3').
        action: 'confirm' to execute the transfer, or 'cancel' to reject/abort the transfer.

    Returns:
        A dictionary containing the finalized transaction receipt (transaction_id, remaining balance) or cancellation message.
    """
    from services.transfer_service import transfer_service

    args = {
        "confirmation_id": confirmation_id,
        "action": action,
    }

    return observability.trace_tool_execution(
        tool_name="confirm_transfer",
        arguments=args,
        execution_func=lambda: transfer_service.confirm_transfer(**args),
    )


def transfer_money(
    source_account_id: str = mockdata.DEFAULT_USER_ACCOUNT,
    destination_account_id: str = "",
    recipient: str = "",
    amount: float = 0.0,
    remarks: str = "",
    confirmed_account_id: str = "",
    auto_confirm: bool = False,
) -> Dict[str, Any]:
    """
    Convenience wrapper for money transfers.
    By default (auto_confirm=False), invokes initiate_transfer to enforce the Stage 3 Human-in-the-Loop harness.
    If auto_confirm=True, confirms immediately upon successful policy verification.
    """
    init_res = initiate_transfer(
        source_account_id=source_account_id,
        recipient=recipient or destination_account_id,
        destination_account_id=destination_account_id,
        amount=amount,
        remarks=remarks,
        confirmed_account_id=confirmed_account_id,
    )
    if not auto_confirm or not init_res.get("success"):
        return init_res

    conf_res = confirm_transfer(
        confirmation_id=init_res["confirmation_id"],
        action="confirm",
    )
    conf_res["policy_check"] = "PASSED"
    return conf_res


def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
    """
    Check the current status and details of a previous transaction by its transaction ID.

    Args:
        transaction_id: The unique transaction identifier (e.g., 'TXN1001', 'TXN1002', 'TXN1003').

    Returns:
        A dictionary containing status ('COMPLETED', 'PENDING', 'FAILED'), amount in ₹, source, destination, and timestamp.
    """
    return observability.trace_tool_execution(
        tool_name="get_transaction_status",
        arguments={"transaction_id": transaction_id},
        execution_func=lambda: bank_db.get_transaction_status(transaction_id),
    )


# List of tool functions exposed to the Gemini model
BANKING_TOOLS = [
    get_balance,
    find_beneficiaries,
    initiate_transfer,
    confirm_transfer,
    get_transaction_status,
    transfer_money,
]
