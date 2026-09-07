"""
Transfer Service & Human-in-the-Loop (HITL) Harness.
Decouples financial transfer into a two-phase authorization pattern:
1. initiate_transfer: Evaluates policies and creates pending confirmation request.
2. confirm_transfer: Executes transaction only upon explicit human approval.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import uuid
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.policy_service import evaluate_transfer_policy
from src.bank_db import bank_db
from src import mockdata


@dataclass
class PendingTransfer:
    """Represents a transfer awaiting human authorization."""
    confirmation_id: str
    source_account_id: str
    destination_account_id: str
    recipient_name: str
    bank_name: str
    amount: float
    currency: str
    currency_symbol: str
    remarks: str
    created_at: str
    expires_at: str
    status: str = "PENDING_CONFIRMATION"  # PENDING_CONFIRMATION, CONFIRMED, CANCELLED, EXPIRED
    transaction_id: Optional[str] = None


class TransferHarnessService:
    """Manages pending transfer authorizations for Human-in-the-Loop workflow."""

    def __init__(self):
        self.pending_transfers: Dict[str, PendingTransfer] = {}

    def initiate_transfer(
        self,
        source_account_id: str = mockdata.DEFAULT_USER_ACCOUNT,
        recipient: str = "",
        destination_account_id: str = "",
        amount: float = 0.0,
        remarks: str = "",
        confirmed_account_id: str = "",
    ) -> Dict[str, Any]:
        """
        Stage 3 Step 1: Initiate transfer and raise human confirmation.
        Evaluates Stage 2 policy harness. If policies pass, registers a pending transfer.
        Does NOT move any funds yet.
        """
        target_query = destination_account_id or recipient
        confirmation_acc = confirmed_account_id or (
            destination_account_id if destination_account_id.startswith("ACC") else ""
        )

        # 1. Evaluate Stage 2 Policy Guardrails
        decision = evaluate_transfer_policy(
            source_account_id=source_account_id,
            recipient=target_query,
            amount=amount,
            confirmed_account_id=confirmation_acc if confirmation_acc else None,
        )

        # If any policy fails or requires ambiguous resolution, return immediately
        if not decision.is_allowed:
            return {
                "success": False,
                "status": "POLICY_REJECTED",
                "policy_code": decision.policy_code,
                "requires_verification": decision.requires_confirmation,
                "requires_confirmation": decision.requires_confirmation,
                "candidate_beneficiaries": decision.candidate_beneficiaries,
                "message": decision.message,
            }

        # 2. Policies passed -> Generate pending confirmation request
        now = datetime.now()
        confirmation_id = f"CONF-{uuid.uuid4().hex[:6].upper()}"
        expires_at = (now + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        created_at_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # Lookup destination bank name for display
        dest_account = bank_db.get_account(decision.resolved_account_id)
        bank_name = dest_account.get("bank_name", "Registered Bank") if dest_account else "Registered Bank"

        source_acc = bank_db.get_account(source_account_id)
        symbol = source_acc.get("currency_symbol", "₹") if source_acc else "₹"
        currency = source_acc.get("currency", "INR") if source_acc else "INR"

        pending = PendingTransfer(
            confirmation_id=confirmation_id,
            source_account_id=source_account_id,
            destination_account_id=decision.resolved_account_id,
            recipient_name=decision.recipient_name or target_query,
            bank_name=bank_name,
            amount=amount,
            currency=currency,
            currency_symbol=symbol,
            remarks=remarks or "Fund Transfer",
            created_at=created_at_str,
            expires_at=expires_at,
            status="PENDING_CONFIRMATION",
        )
        self.pending_transfers[confirmation_id] = pending

        return {
            "success": True,
            "status": "PENDING_CONFIRMATION",
            "confirmation_id": confirmation_id,
            "source_account_id": source_account_id,
            "recipient_name": pending.recipient_name,
            "destination_account_id": pending.destination_account_id,
            "destination_bank": pending.bank_name,
            "amount": amount,
            "currency": currency,
            "currency_symbol": symbol,
            "formatted_amount": f"{symbol}{amount:,.2f}",
            "remarks": pending.remarks,
            "expires_at": expires_at,
            "human_in_the_loop": {
                "requires_user_confirmation": True,
                "prompt": (
                    f"Please confirm: Transfer {symbol}{amount:,.2f} to {pending.recipient_name} "
                    f"({pending.destination_account_id} at {pending.bank_name}) with remarks '{pending.remarks}'. "
                    f"Confirmation ID: {confirmation_id}. Reply YES to confirm or NO to cancel."
                ),
            },
            "message": f"Transfer of {symbol}{amount:,.2f} initiated. Awaiting human confirmation.",
        }

    def confirm_transfer(
        self,
        confirmation_id: str,
        action: str = "confirm",
    ) -> Dict[str, Any]:
        """
        Stage 3 Step 2: Human-in-the-loop confirmation.
        Executes or cancels the transfer based on human decision.

        Args:
            confirmation_id: Unique identifier generated by initiate_transfer.
            action: 'confirm' to execute the transfer, 'cancel' to discard it.
        """
        clean_id = (confirmation_id or "").strip().upper()
        pending = self.pending_transfers.get(clean_id)

        if not pending:
            return {
                "success": False,
                "status": "INVALID_CONFIRMATION_ID",
                "error": f"No pending transfer found for confirmation ID '{confirmation_id}'. Please initiate a transfer first.",
            }

        # Check if already finalized
        if pending.status != "PENDING_CONFIRMATION":
            return {
                "success": False,
                "status": "ALREADY_PROCESSED",
                "error": f"Transfer '{clean_id}' has already been processed with status: {pending.status}.",
            }

        # Check expiration
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if now_str > pending.expires_at:
            pending.status = "EXPIRED"
            return {
                "success": False,
                "status": "EXPIRED",
                "error": f"Transfer confirmation '{clean_id}' has expired. Please initiate a new transfer request.",
            }

        clean_action = (action or "confirm").strip().lower()

        # Human rejected / cancelled the transfer
        if clean_action in ["cancel", "no", "reject", "deny", "abort"]:
            pending.status = "CANCELLED"
            return {
                "success": True,
                "status": "CANCELLED",
                "confirmation_id": clean_id,
                "message": f"Transfer of {pending.currency_symbol}{pending.amount:,.2f} to {pending.recipient_name} was CANCELLED by user. No funds were debited.",
            }

        # Human confirmed -> Execute transfer against bank ledger
        transfer_result = bank_db.transfer_money(
            source_account_id=pending.source_account_id,
            destination_account_id=pending.destination_account_id,
            amount=pending.amount,
            remarks=pending.remarks,
        )

        if not transfer_result.get("success"):
            # Transfer failed at DB execution level (e.g. state changed in between)
            pending.status = "FAILED"
            return {
                "success": False,
                "status": "EXECUTION_FAILED",
                "confirmation_id": clean_id,
                "error": transfer_result.get("error", "Database transfer execution failed."),
            }

        pending.status = "CONFIRMED"
        pending.transaction_id = transfer_result.get("transaction_id")

        return {
            "success": True,
            "status": "COMPLETED",
            "confirmation_id": clean_id,
            "transaction_id": pending.transaction_id,
            "source_account_id": pending.source_account_id,
            "destination_account_id": pending.destination_account_id,
            "recipient_name": pending.recipient_name,
            "destination_bank": pending.bank_name,
            "amount": pending.amount,
            "currency": pending.currency,
            "currency_symbol": pending.currency_symbol,
            "formatted_amount": f"{pending.currency_symbol}{pending.amount:,.2f}",
            "remaining_balance": transfer_result.get("remaining_balance"),
            "remarks": pending.remarks,
            "timestamp": transfer_result.get("timestamp"),
            "message": (
                f"Transfer of {pending.currency_symbol}{pending.amount:,.2f} to {pending.recipient_name} "
                f"successfully executed! Transaction ID: {pending.transaction_id}. "
                f"Remaining balance: {pending.currency_symbol}{transfer_result.get('remaining_balance'):,.2f}."
            ),
        }

    def get_pending_transfer(self, confirmation_id: str) -> Optional[PendingTransfer]:
        return self.pending_transfers.get((confirmation_id or "").strip().upper())


# Global singleton service
transfer_service = TransferHarnessService()
