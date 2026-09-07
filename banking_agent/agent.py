"""
Google ADK Banking Agent definition.
Can be run via:
  adk run banking_agent
  adk web .
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from google.adk.agents import Agent
from src.prompts import SYSTEM_PROMPT
from src.bank_tools import (
    get_balance,
    find_beneficiaries,
    transfer_money,
    get_transaction_status,
)

import os

# Root agent definition required by Google ADK
root_agent = Agent(
    name="banking_agent",
    description="Retail banking assistant for account balances, beneficiary queries, money transfers, and transaction status.",
    model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    instruction=SYSTEM_PROMPT,
    tools=[
        get_balance,
        find_beneficiaries,
        transfer_money,
        get_transaction_status,
    ],
)
