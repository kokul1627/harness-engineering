"""
Policy Service & Guardrail Harness for Banking Operations.
Enforces safety, validation, and confirmation policies before financial execution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bank_db import bank_db
from src import mockdata


@dataclass
class PolicyDecision:
    """Represents the outcome of evaluating banking policies."""
    is_allowed: bool
    policy_code: str
    message: str
    requires_confirmation: bool = False
    resolved_account_id: Optional[str] = None
    recipient_name: Optional[str] = None
    candidate_beneficiaries: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_allowed": self.is_allowed,
            "policy_code": self.policy_code,
            "message": self.message,
            "requires_confirmation": self.requires_confirmation,
            "resolved_account_id": self.resolved_account_id,
            "recipient_name": self.recipient_name,
            "candidate_beneficiaries": self.candidate_beneficiaries,
        }


def resolve_beneficiary(
    source_account_id: str,
    recipient_query: str,
    confirmed_account_id: Optional[str] = None,
) -> Tuple[int, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Match recipient against registered beneficiaries for the source account.

    Policies enforced:
    - If confirmed_account_id is provided, look for that exact account among candidates.
    - If recipient_query matches an exact account_id, return that match.
    - Otherwise perform case-insensitive name & nickname matching.

    Returns:
        (matches_count, candidate_list, selected_beneficiary_or_None)
    """
    beneficiaries_resp = bank_db.get_beneficiaries(source_account_id)
    beneficiaries = beneficiaries_resp.get("beneficiaries", [])

    query = (recipient_query or "").strip().lower()

    # 1. If explicit confirmation account ID is provided, verify it exists in beneficiaries
    if confirmed_account_id:
        target_acc = confirmed_account_id.strip().upper()
        for b in beneficiaries:
            if b.get("account_id", "").upper() == target_acc:
                return (1, [b], b)
        return (0, [], None)

    # 2. Direct Account ID match
    query_upper = query.upper()
    direct_acc_matches = [
        b for b in beneficiaries if b.get("account_id", "").upper() == query_upper
    ]
    if len(direct_acc_matches) == 1:
        return (1, direct_acc_matches, direct_acc_matches[0])

    # 3. Match by name or nickname
    matches = []
    for b in beneficiaries:
        name = b.get("name", "").lower()
        nickname = b.get("nickname", "").lower()
        if query == name or query == nickname:
            matches.append(b)
        elif query in name or query in nickname:
            matches.append(b)

    # Deduplicate matches by beneficiary account_id
    unique_matches = []
    seen_accounts = set()
    for m in matches:
        acc = m.get("account_id")
        if acc not in seen_accounts:
            seen_accounts.add(acc)
            unique_matches.append(m)

    match_count = len(unique_matches)
    selected = unique_matches[0] if match_count == 1 else None

    return (match_count, unique_matches, selected)


def check_transfer_limits_and_status(
    source_account_id: str,
    amount: float,
) -> Tuple[bool, str, str]:
    """
    Validates account status and transaction limits:
    - Policy 1: amount > 0
    - Policy 2: account status == 'ACTIVE'
    - Policy 3: amount <= account balance
    - Policy 4: account transfer < daily limit (cumulative daily transfers + amount <= daily limit)

    Returns:
        (is_allowed, policy_code, message)
    """
    # Policy: amount > 0
    if amount is None or amount <= 0:
        return (
            False,
            "INVALID_AMOUNT",
            f"Transfer amount must be strictly greater than ₹0.00. (Requested: ₹{amount})",
        )

    source = bank_db.get_account(source_account_id)
    if not source:
        return (
            False,
            "ACCOUNT_NOT_FOUND",
            f"Source account '{source_account_id}' does not exist.",
        )

    # Policy: account status = active
    account_status = source.get("status", "").upper()
    if account_status != "ACTIVE":
        return (
            False,
            "INACTIVE_ACCOUNT",
            f"Transfer denied: Account '{source_account_id}' status is '{account_status}'. Transfers are only permitted on ACTIVE accounts.",
        )

    # Policy: amount <= account balance
    current_balance = float(source.get("balance", 0.0))
    if amount > current_balance:
        return (
            False,
            "INSUFFICIENT_FUNDS",
            f"Transfer denied: Insufficient funds. Requested transfer: ₹{amount:,.2f}, but current balance is ₹{current_balance:,.2f}.",
        )

    # Policy: account transfer < daily limit
    daily_limit = float(source.get("daily_limit", mockdata.DEFAULT_DAILY_LIMIT))
    transferred_today = bank_db.get_daily_transferred_amount(source_account_id)
    remaining_daily_limit = max(0.0, daily_limit - transferred_today)

    if (transferred_today + amount) > daily_limit:
        return (
            False,
            "DAILY_LIMIT_EXCEEDED",
            f"Transfer denied: Daily transfer limit exceeded. Daily limit: ₹{daily_limit:,.2f}, transferred today: ₹{transferred_today:,.2f}, remaining allowance: ₹{remaining_daily_limit:,.2f}. Requested transfer: ₹{amount:,.2f}.",
        )

    return (True, "APPROVED", "Transfer limits and account status verified successfully.")


def evaluate_transfer_policy(
    source_account_id: str,
    recipient: str,
    amount: float,
    confirmed_account_id: Optional[str] = None,
) -> PolicyDecision:
    """
    Comprehensive Policy Harness evaluation for money transfers.

    Execution Flow:
    1. Amount Policy: amount > 0
    2. Account Status Policy: source account exists & status == 'ACTIVE'
    3. Beneficiary Matching:
       - If no match (matches == 0): REJECT transfer.
       - If matches > 1: REQUIRE USER CONFIRMATION (returns candidate list).
       - If matches == 1: Resolved.
    4. Financial Limits Policy:
       - amount <= balance
       - amount + transferred_today <= daily_limit

    Returns:
        PolicyDecision object with detailed policy outcomes.
    """
    # Policy 1: amount > 0
    if amount is None or amount <= 0:
        return PolicyDecision(
            is_allowed=False,
            policy_code="INVALID_AMOUNT",
            message=f"Transfer denied: Transfer amount must be strictly greater than ₹0.00. (Requested: ₹{amount})",
            requires_confirmation=False,
        )

    # Policy 2: account status = active
    source = bank_db.get_account(source_account_id)
    if not source:
        return PolicyDecision(
            is_allowed=False,
            policy_code="ACCOUNT_NOT_FOUND",
            message=f"Transfer denied: Source account '{source_account_id}' does not exist.",
            requires_confirmation=False,
        )

    account_status = source.get("status", "").upper()
    if account_status != "ACTIVE":
        return PolicyDecision(
            is_allowed=False,
            policy_code="INACTIVE_ACCOUNT",
            message=f"Transfer denied: Account '{source_account_id}' status is '{account_status}'. Transfers are only permitted on ACTIVE accounts.",
            requires_confirmation=False,
        )

    # Policy 3: Beneficiary Resolution
    match_count, candidates, selected = resolve_beneficiary(
        source_account_id=source_account_id,
        recipient_query=recipient,
        confirmed_account_id=confirmed_account_id,
    )

    # If no match -> no transfer
    if match_count == 0:
        return PolicyDecision(
            is_allowed=False,
            policy_code="NO_MATCH",
            message=f"Transfer denied: No registered beneficiary matches '{recipient}'. Transfers can only be made to registered beneficiaries.",
            requires_confirmation=False,
            candidate_beneficiaries=[],
        )

    # If matches > 1 -> ask for verification & confirm user
    if match_count > 1:
        candidate_summary = [
            f"{c.get('name')} (Account: {c.get('account_id')}, Bank: {c.get('bank_name')})"
            for c in candidates
        ]
        return PolicyDecision(
            is_allowed=False,
            policy_code="AMBIGUOUS_MATCH",
            message=(
                f"Verification required: Multiple beneficiaries ({match_count}) found matching '{recipient}': "
                f"{'; '.join(candidate_summary)}. "
                f"Please ask the user to confirm the specific account number or full name before proceeding."
            ),
            requires_confirmation=True,
            candidate_beneficiaries=candidates,
        )

    resolved_acc = selected.get("account_id")
    recipient_name = selected.get("name")

    # Policy 4: amount <= account balance
    current_balance = float(source.get("balance", 0.0))
    if amount > current_balance:
        return PolicyDecision(
            is_allowed=False,
            policy_code="INSUFFICIENT_FUNDS",
            message=f"Transfer denied: Insufficient funds. Requested transfer: ₹{amount:,.2f}, but current balance is ₹{current_balance:,.2f}.",
            requires_confirmation=False,
            resolved_account_id=resolved_acc,
            recipient_name=recipient_name,
            candidate_beneficiaries=[selected],
        )

    # Policy 5: account transfer < daily limit
    daily_limit = float(source.get("daily_limit", mockdata.DEFAULT_DAILY_LIMIT))
    transferred_today = bank_db.get_daily_transferred_amount(source_account_id)
    remaining_daily_limit = max(0.0, daily_limit - transferred_today)

    if (transferred_today + amount) > daily_limit:
        return PolicyDecision(
            is_allowed=False,
            policy_code="DAILY_LIMIT_EXCEEDED",
            message=f"Transfer denied: Daily transfer limit exceeded. Daily limit: ₹{daily_limit:,.2f}, transferred today: ₹{transferred_today:,.2f}, remaining allowance: ₹{remaining_daily_limit:,.2f}. Requested transfer: ₹{amount:,.2f}.",
            requires_confirmation=False,
            resolved_account_id=resolved_acc,
            recipient_name=recipient_name,
            candidate_beneficiaries=[selected],
        )

    # All policies satisfied!
    return PolicyDecision(
        is_allowed=True,
        policy_code="APPROVED",
        message=f"All transfer policies verified. Recipient resolved to {recipient_name} ({resolved_acc}).",
        requires_confirmation=False,
        resolved_account_id=resolved_acc,
        recipient_name=recipient_name,
        candidate_beneficiaries=[selected],
    )
