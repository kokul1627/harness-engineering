# Naive Banking Agent (Stage 1: No Harness)

A conversational AI banking agent developed using the **Google GenAI SDK** and **Gemini Flash**. 

This repository serves as **Stage 1** of a multi-stage **Harness Engineering** project:
- **Stage 1 (Current)**: **Naive Agent (No Harness)** — Direct tool calling with LLM, establishing baseline behavior and measuring tool accuracy.
- **Subsequent Stages**: Test harness, safety guardrail harness, evaluation harness, and mock transaction harnesses.

---

## 🛠️ Features & Banking Tools

The agent is equipped with four core banking tools operating against an in-memory banking ledger:

1. `get_balance(account_id: str)`
   - Fetches real-time account balance, currency, and account status.
2. `get_beneficiaries(account_id: str)`
   - Lists registered beneficiaries (name, account number, bank, nickname) to whom funds can be sent.
3. `transfer_money(source_account_id: str, destination_account_id: str, amount: float, remarks: str)`
   - Validates balance, debits source account, credits destination account, and generates a transaction record.
4. `get_transaction_status(transaction_id: str)`
   - Retrieves transaction details and status (`COMPLETED`, `PENDING`, `FAILED`).

---

## 📁 Project Structure

```
harness engineering/
├── src/
│   ├── __init__.py          # Exports core components
│   ├── prompts.py           # System prompt (4 tools, INR ₹ format)
│   ├── mockdata.py          # Indian retail banking demo data
│   ├── bank_tools.py        # Banking tool declarations for Gemini
│   ├── bank_db.py           # In-memory bank state & transaction ledger
│   └── naive_agent.py       # Google GenAI SDK Agent loop
├── tests/
│   ├── __init__.py
│   └── test_banking_agent.py# Automated verification test suite
├── main.py                  # Interactive CLI entrypoint
├── requirements.txt         # Project dependencies
├── .env.example             # Environment variable template
├── .env                     # Local environment file
├── .gitignore               # Git ignore rules
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your Gemini API Key:
```env
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
DEMO_ACCOUNT_ID=ACC1001
```

### 2. Activate Virtual Environment
On Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Run with Google ADK Web Interface (Dev UI)
To launch Google's official default ADK Web UI in your browser:
```powershell
.\.venv\Scripts\adk.exe web .
```
Or specify a custom port:
```powershell
.\.venv\Scripts\adk.exe web --port 8000 .
```
Then open your browser to **http://127.0.0.1:8000** (or http://127.0.0.1:8000/dev-ui/).

### 4. Run with Google ADK Terminal CLI
```powershell
.\.venv\Scripts\adk.exe run banking_agent
```

### 5. Run Custom Interactive CLI
```powershell
.\.venv\Scripts\python.exe main.py
```

### 6. Run Automated Tests
```powershell
.\.venv\Scripts\python.exe tests/test_banking_agent.py
```

---

## 💡 Example Conversation

```text
You: What is my current balance?
Agent: Your current account balance for account ACC1001 is $5,000.00 USD.

You: Can you show me my beneficiaries?
Agent: Here are your registered beneficiaries:
1. Alice Johnson (Account: ACC2001, Metro Bank)
2. Bob Williams (Account: ACC2002, Global Trust)
3. Charlie Brown (Account: ACC2003, Apex Credit Union)

You: Transfer $250 to Bob for project design
Agent: I have successfully transferred $250.00 USD to Bob Williams (ACC2002) with remarks "project design". 
Transaction ID: TXN4B1A8C. 
Your remaining balance is $4,750.00 USD.

You: Check the status of transaction TXN1001
Agent: Transaction TXN1001 of $150.00 to Alice Johnson is COMPLETED.
```
