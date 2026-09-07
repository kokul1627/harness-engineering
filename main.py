"""
Interactive CLI for Naive Banking Agent.
Allows testing the agent live in the terminal.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.naive_agent import NaiveBankingAgent
from src import mockdata


def print_banner():
    account = mockdata.ACCOUNTS.get(mockdata.DEFAULT_USER_ACCOUNT, {})
    owner = account.get("owner_name", "Priya Sharma")
    balance = account.get("balance", 75000.0)
    bank_name = account.get("bank_name", "HDFC Bank")

    print("=" * 65)
    print("         🏦  NAIVE BANKING AGENT (STAGE 1: NO HARNESS)  🏦         ")
    print("=" * 65)
    print(f"Powered by Google GenAI SDK & Gemini Flash")
    print(f"Logged in: {owner} ({mockdata.DEFAULT_USER_ACCOUNT}) | {bank_name}")
    print(f"Available Balance: ₹{balance:,.2f}")
    print("\nSupported Tool Actions:")
    print("  • Check balance            (e.g., 'What is my current balance?')")
    print("  • Find beneficiaries       (e.g., 'Who are my saved beneficiaries?')")
    print("  • Transfer money           (e.g., 'Transfer ₹1,500 to Rahul for dinner')")
    print("  • Check transaction status (e.g., 'What is the status of TXN1001?')")
    print("\nType 'exit' or 'quit' to end the session. Type 'reset' to clear chat.")
    print("=" * 65 + "\n")


def main():
    try:
        agent = NaiveBankingAgent()
    except ValueError as e:
        print(f"\n[Configuration Error] {e}")
        print("Please copy .env.example to .env and insert your GEMINI_API_KEY.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Initialization Error] {e}\n")
        sys.exit(1)

    print_banner()

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nThank you for banking with us. Goodbye!\n")
                break

            if user_input.lower() in ["reset", "clear"]:
                agent.reset_chat()
                print("\n[Conversation history reset]\n")
                continue

            print("\n[Banking Agent is thinking...]")
            response = agent.send_message(user_input)
            print(f"\nAgent:\n{response}\n")
            print("-" * 65)

        except KeyboardInterrupt:
            print("\n\nSession terminated by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n[Error]: {e}\n")


if __name__ == "__main__":
    main()
