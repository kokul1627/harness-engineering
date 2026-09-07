"""
In-memory Banking Database and State Management.
Loads initial mock data from mockdata.py (in Indian Rupees ₹).
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid

try:
    from . import mockdata
except ImportError:
    import mockdata


class BankingDatabase:
    """Mock Banking Store providing state and ledger during runtime."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the database to initial mockdata state."""
        # Deep copy mock accounts
        self.accounts: Dict[str, Dict] = {
            acc_id: dict(data) for acc_id, data in mockdata.ACCOUNTS.items()
        }
        # Deep copy mock beneficiaries
        self.beneficiaries: Dict[str, List[Dict]] = {
            acc_id: [dict(b) for b in ben_list]
            for acc_id, ben_list in mockdata.BENEFICIARIES.items()
        }
        # Deep copy mock transactions
        self.transactions: Dict[str, Dict] = {
            txn_id: dict(data) for txn_id, data in mockdata.TRANSACTIONS.items()
        }

    def get_account(self, account_id: str) -> Optional[Dict]:
        return self.accounts.get(account_id)

    def get_balance(self, account_id: str) -> Dict:
        account = self.get_account(account_id)
        if not account:
            return {
                "success": False,
                "error": f"Account '{account_id}' not found."
            }
        return {
            "success": True,
            "account_id": account["account_id"],
            "owner_name": account["owner_name"],
            "balance": round(account["balance"], 2),
            "currency": account["currency"],
            "currency_symbol": account.get("currency_symbol", "₹"),
            "status": account["status"],
        }

    def find_beneficiaries(self, account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict:
        beneficiaries_list = self.beneficiaries.get(account_id, [])
        return {
            "success": True,
            "account_id": account_id,
            "beneficiaries": beneficiaries_list,
        }

    def get_beneficiaries(self, account_id: str = mockdata.DEFAULT_USER_ACCOUNT) -> Dict:
        """Alias for find_beneficiaries."""
        return self.find_beneficiaries(account_id)

    def transfer_money(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: float,
        remarks: str = "",
    ) -> Dict:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        txn_id = f"TXN{uuid.uuid4().hex[:6].upper()}"

        # Validations
        if amount <= 0:
            return {
                "success": False,
                "transaction_id": txn_id,
                "error": "Transfer amount must be greater than zero.",
            }

        source = self.get_account(source_account_id)
        if not source:
            return {
                "success": False,
                "transaction_id": txn_id,
                "error": f"Source account '{source_account_id}' does not exist.",
            }

        dest = self.get_account(destination_account_id)
        if not dest:
            return {
                "success": False,
                "transaction_id": txn_id,
                "error": f"Destination account '{destination_account_id}' does not exist.",
            }

        if source["balance"] < amount:
            txn = {
                "transaction_id": txn_id,
                "source_account_id": source_account_id,
                "destination_account_id": destination_account_id,
                "recipient_name": dest.get("owner_name", ""),
                "amount": amount,
                "currency": source["currency"],
                "status": "FAILED",
                "remarks": remarks,
                "timestamp": now_str,
                "error_message": "Insufficient funds",
            }
            self.transactions[txn_id] = txn
            return {
                "success": False,
                "transaction_id": txn_id,
                "status": "FAILED",
                "error": f"Insufficient balance. Current balance is ₹{source['balance']:,.2f}, transfer requested: ₹{amount:,.2f}.",
            }

        # Execute transfer
        source["balance"] -= amount
        dest["balance"] += amount

        txn = {
            "transaction_id": txn_id,
            "source_account_id": source_account_id,
            "destination_account_id": destination_account_id,
            "recipient_name": dest.get("owner_name", ""),
            "amount": amount,
            "currency": source["currency"],
            "status": "COMPLETED",
            "remarks": remarks,
            "timestamp": now_str,
        }
        self.transactions[txn_id] = txn

        return {
            "success": True,
            "transaction_id": txn_id,
            "source_account_id": source_account_id,
            "destination_account_id": destination_account_id,
            "recipient_name": dest.get("owner_name", ""),
            "amount": amount,
            "currency": source["currency"],
            "currency_symbol": source.get("currency_symbol", "₹"),
            "status": "COMPLETED",
            "remarks": remarks,
            "timestamp": now_str,
            "remaining_balance": round(source["balance"], 2),
        }

    def get_transaction_status(self, transaction_id: str) -> Dict:
        txn = self.transactions.get(transaction_id)
        if not txn:
            return {
                "success": False,
                "transaction_id": transaction_id,
                "error": f"Transaction '{transaction_id}' not found.",
            }
        return {
            "success": True,
            **txn,
        }


# Global singleton instance
bank_db = BankingDatabase()
