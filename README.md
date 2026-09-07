# Retail Banking AI Agent (Harness Engineering Stages 1 - 4)

A conversational AI banking agent developed using the **Google GenAI SDK**, **Gemini 3.6 Flash**, and **Google Agent Development Kit (ADK)**. 

This project demonstrates the progressive engineering evolution across **4 Stages of Harness Engineering**:
1. **Stage 1: Naive Baseline Agent** — Raw LLM tool calling with no harness.
2. **Stage 2: Policy & Guardrail Harness** — Deterministic validation (beneficiary resolution, positive amount, active status, balance check, daily limits).
3. **Stage 3: Human-in-the-Loop (HITL) Harness** — Two-phase commitment (`initiate_transfer` $\rightarrow$ `confirm_transfer`) requiring explicit human authorization.
4. **Stage 4: Observability & Monitoring Harness** — Real-time workflow tracing, latency tracking, and audit logging to monitor the agent and troubleshoot production issues.

> 📖 **Comprehensive Documentation**: See [HARNESS_STAGES.md](file:///c:/mppeapril/applications/collections/genai%20projects/harness%20engineering/HARNESS_STAGES.md) for full architectural explanations, sequence diagrams, and production diagnostic guides.

---

## 📁 Project Structure

```
harness engineering/
├── services/                             # Harness & Business Logic
│   ├── __init__.py
│   ├── policy_service.py                 # Stage 2: Policy & Guardrail Harness
│   ├── transfer_service.py               # Stage 3: Human-in-the-Loop (HITL) Harness
│   └── observability_service.py          # Stage 4: Observability & Monitoring Harness
├── logs/
│   └── agent_workflow.jsonl              # Structured audit & telemetry logs
├── src/
│   ├── __init__.py                       # Core package exports
│   ├── prompts.py                        # System prompt with HITL 2-step protocol
│   ├── mockdata.py                       # Indian retail banking demo data
│   ├── bank_tools.py                     # Traced banking tools
│   ├── bank_db.py                        # In-memory bank state & ledger
│   └── naive_agent.py                    # Direct Agent loop
├── tests/
│   ├── __init__.py
│   ├── test_policy_service.py            # Unit tests for Stage 2 policies
│   ├── test_hitl_transfer.py             # Unit tests for Stage 3 HITL harness
│   └── test_banking_agent.py             # Agent integration tests
├── banking_agent/                        # Google ADK agent package
│   ├── __init__.py
│   └── agent.py
├── HARNESS_STAGES.md                     # Comprehensive 4-Stage Architectural Guide
├── main.py                               # CLI runner
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## 🤝 Stage 3: Human-in-the-Loop (HITL) Protocol

1. **Phase 1: `initiate_transfer`**
   - Validates all Stage 2 policies (beneficiary matching, amount > 0, active account, balance, daily limits).
   - Generates a unique `confirmation_id` (e.g. `CONF-9B2A1C`) with an expiration timer.
   - **Zero funds are moved.** The agent presents the transfer details and asks the user to confirm.
2. **Phase 2: `confirm_transfer`**
   - If user replies YES / confirms: Executes the transfer on the bank ledger, debits balance, and returns transaction receipt.
   - If user replies NO / cancels: Marks request as `CANCELLED`, leaving account balance completely untouched.
   - Replay prevention: Once processed, a `confirmation_id` cannot be reused.

---

## 🛡️ Stage 2 Policy Rules

Before any money is transferred, `services/policy_service.py` evaluates:
1. **`amount > 0`**: Transfer amount must be positive.
2. **`account status == 'ACTIVE'`**: Sender account must be active (not FROZEN or CLOSED).
3. **Beneficiary Match**:
   - `matches == 0`: No match $\rightarrow$ Transfer denied.
   - `matches > 1`: Ambiguous $\rightarrow$ Requires user confirmation of specific account.
   - `matches == 1`: Exactly 1 match $\rightarrow$ Transfer permitted.
4. **`amount <= balance`**: Cannot exceed available balance.
5. **`transferred_today + amount <= daily_limit`**: Cumulative daily transfers must stay within daily allowance.

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
