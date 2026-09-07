"""
Banking Tools for Gemini Function Calling.
These functions interface directly with the mock bank database.
"""
from typing import Dict, Any

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
    amount: float = 0.0,
    remarks: str = "",
) -> Dict[str, Any]:
    """
    Execute a money transfer from a source account to a destination account.

    Args:
        source_account_id: The sender's account identifier (defaults to 'ACC1001').
        destination_account_id: The recipient's account identifier (e.g., 'ACC2001', 'ACC2002', 'ACC2003').
        amount: The monetary amount in INR (₹) to transfer (must be greater than 0).
        remarks: Optional description or note for the transfer (e.g., 'dinner', 'rent').

    Returns:
        A dictionary with the transaction result, including transaction_id, status, and remaining balance.
    """
    return bank_db.transfer_money(
        source_account_id=source_account_id,
        destination_account_id=destination_account_id,
        amount=amount,
        remarks=remarks,
    )


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
