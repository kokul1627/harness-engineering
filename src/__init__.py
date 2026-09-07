"""
Banking Agent Core Package.
"""

from .prompts import SYSTEM_PROMPT
from .mockdata import ACCOUNTS, BENEFICIARIES, TRANSACTIONS, DEFAULT_USER_ACCOUNT
from .bank_db import bank_db, BankingDatabase
from .bank_tools import (
    BANKING_TOOLS,
    get_balance,
    find_beneficiaries,
    transfer_money,
    get_transaction_status,
)
from .naive_agent import NaiveBankingAgent

__all__ = [
    "SYSTEM_PROMPT",
    "ACCOUNTS",
    "BENEFICIARIES",
    "TRANSACTIONS",
    "DEFAULT_USER_ACCOUNT",
    "bank_db",
    "BankingDatabase",
    "BANKING_TOOLS",
    "get_balance",
    "find_beneficiaries",
    "transfer_money",
    "get_transaction_status",
    "NaiveBankingAgent",
]
