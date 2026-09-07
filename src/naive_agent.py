"""
Naive Banking Agent using Google GenAI SDK.
Stage 1: Direct function calling with Gemini Flash without an evaluation harness or guardrails.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

try:
    from .prompts import SYSTEM_PROMPT
    from .bank_tools import (
        BANKING_TOOLS,
        get_balance,
        find_beneficiaries,
        transfer_money,
        get_transaction_status,
    )
    from . import mockdata
except ImportError:
    from prompts import SYSTEM_PROMPT
    from bank_tools import (
        BANKING_TOOLS,
        get_balance,
        find_beneficiaries,
        transfer_money,
        get_transaction_status,
    )
    import mockdata

# Load environment variables
load_dotenv()


class NaiveBankingAgent:
    """
    Naive Banking Agent.
    Executes tool-calling directly with Gemini Flash without any harness layer.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        default_account_id: str = mockdata.DEFAULT_USER_ACCOUNT,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found! Please set GEMINI_API_KEY in your .env file."
            )

        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.default_account_id = default_account_id or os.getenv("DEMO_ACCOUNT_ID", mockdata.DEFAULT_USER_ACCOUNT)

        # Initialize Google GenAI client
        self.client = genai.Client(api_key=self.api_key)

        # Mapping of tool names to callable functions
        self.tool_map = {
            "get_balance": get_balance,
            "find_beneficiaries": find_beneficiaries,
            "transfer_money": transfer_money,
            "get_transaction_status": get_transaction_status,
        }

        # Initialize conversation session
        self.chat = self._create_chat_session()

    def _create_chat_session(self):
        """Create a new chat session with banking tools enabled."""
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=BANKING_TOOLS,
            temperature=0.1,
        )
        return self.client.chats.create(
            model=self.model_name,
            config=config,
        )

    def reset_chat(self):
        """Reset the conversation session."""
        self.chat = self._create_chat_session()

    def send_message(self, user_input: str) -> str:
        """
        Send a user message to the agent, allowing automatic tool calls.
        Returns the final response text.
        """
        response = self.chat.send_message(user_input)
        return response.text
