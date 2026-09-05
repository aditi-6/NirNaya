# NirNaya

### Evidence-First Settlement Intelligence

**PS-8 — Settlement Q&A Agent for Fintech Support**

> Don't just ask where the money went. Ask what the evidence says.

NirNaya is an evidence-first settlement investigation agent that traces a transaction across gateway, bank, and ledger records, reconciles the available evidence, identifies the settlement status and root cause, and explains the result in plain English.

The key distinction is simple: **the evidence decides. The AI explains.**

---

## Why NirNaya?

Settlement issues rarely exist in a single system. A payment may be successfully captured by the gateway, marked as processed for settlement, present in the bank with a matching UTR — but still missing from the ledger. Or the records may contradict each other.

Answering "why hasn't this settlement reached the merchant?" usually means manually checking multiple systems and reconstructing the transaction by hand. NirNaya turns that into one evidence-backed investigation.

---

## From Transaction ID to Answer

```text
                TRANSACTION ID
                      |
                      v
        +--------------------------+
        |     MULTI-SOURCE TRACE   |
        |  Gateway | Bank | Ledger |
        +--------------------------+
                      |
                      v
        +--------------------------+
        |      RECONCILIATION      |
        | Match amounts, UTRs,     |
        | statuses & records       |
        +--------------------------+
                      |
                      v
        +--------------------------+
        |       RULE ENGINE        |
        | Status + Root Cause      |
        | Confidence + Severity    |
        +--------------------------+
                      |
                      v
        +--------------------------+
        |      GROUNDED AI         |
        | Explains verified facts  |
        | Never invents evidence   |
        +--------------------------+
                      |
                      v
           INVESTIGATION RESULT
```

---

## The Core Idea

Most AI-powered support tools put the LLM at the center of the decision. NirNaya deliberately does the opposite.

**Financial truth is deterministic.** The backend (`engine/reconciler.py`) decides settlement status, root cause, confidence, severity, evidence, and exceptions — using rule-based logic, not the LLM.

**AI is an explanation layer.** The LLM receives the already-verified investigation result and converts it into a plain-English explanation, a customer-ready reply, and answers to follow-up questions. It does not calculate financial state or override the backend's decision.

This makes NirNaya auditable and resistant to hallucination — if a judge asks "how do you prevent the AI from making up a settlement status," the answer is: it structurally can't, because it never sees raw data, only the backend's already-decided verdict.

---

## What NirNaya Investigates

### Settlement Status

| Status | Meaning |
|---|---|
| `SETTLED` | Evidence supports successful settlement |
| `PENDING` | Settlement is incomplete or awaiting another system |
| `FAILED` | Evidence indicates settlement or payment failure |
| `EXCEPTION` | Evidence is missing, conflicting, or doesn't fit a known pattern confidently |

### Root Cause

Instead of a generic "settlement delayed" message, NirNaya distinguishes between:

```text
SUCCESS
BANK_POSTING_DELAY
LEDGER_SYNC_DELAY
SETTLEMENT_ON_HOLD
BANK_REJECTION
GATEWAY_FAILURE
PARTIAL_SETTLEMENT
AMOUNT_MISMATCH
MISSING_BANK_RECORD
MISSING_LEDGER_RECORD
UTR_MISMATCH
DUPLICATE_BANK_ENTRY
INSUFFICIENT_EVIDENCE
TRANSACTION_NOT_FOUND
```

### Evidence

Every decision is backed by the records that produced it, and missing information is surfaced explicitly rather than silently filled in:

```text
Gateway payment status:  processed
Bank status:             pending
UTR:                     matched between gateway and bank
Ledger status:           pending
```

> Missing evidence is treated as an exception, not silently assumed.

---

## Investigation Example

**Transaction:** `TXN_10021`

```text
STATUS       PENDING
ROOT CAUSE   BANK_POSTING_DELAY
CONFIDENCE   65%
SETTLEMENT   SET_70021
UTR          ICICI322955
```

**Evidence:**
```text
Gateway payment status: processed
Bank status: pending
UTR matched between gateway and bank record.
Ledger status: pending
```

**Exception:**
```text
Bank has not yet confirmed credit; this may resolve within the normal posting window.
```

**Recommended action:**
```text
Wait for standard bank SLA window. If not credited after SLA, escalate with UTR to banking ops.
```

The AI layer turns these verified facts into a plain-English explanation and a customer-ready reply without changing the underlying decision.

---

## Built for Messy Reality

NirNaya is tested against deliberately constructed edge cases, not just the happy path:

| Transaction | Scenario |
|---|---|
| `TXN_10001` | Successful settlement |
| `TXN_10021` | Bank posting delay |
| `TXN_10029` | Bank rejection |
| `TXN_10033` | Gateway failure |
| `TXN_10037` | Settlement on hold |
| `TXN_10041` | Partial settlement |
| `TXN_10045` | Ledger sync delay |
| `TXN_10049` | Amount mismatch |
| `TXN_10052` | Missing bank record |
| `TXN_10055` | Missing ledger record |
| `TXN_10058` | UTR mismatch |
| `TXN_10060` | Duplicate bank entry |
| `TXN_99999` | Transaction not found |

12 constructed scenarios plus the not-found case — 13 test cases in total, all verified passing via `test_all_scenarios.py`.

---

## What You Can Ask NirNaya

**Investigate:**
```text
Transaction: TXN_10021
Why is this settlement pending?
```

**Follow-up (via /api/ask):**
```text
Why does the system think this is a bank delay?
What should the operations team do next?
```

---

## Architecture

```text
                FRONTEND
           HTML / CSS / JS
                   |
                   v
                FLASK (app.py)
                   |
        +----------+----------+
        |                     |
        v                     v
     TRACE                RECONCILE
   (tracer.py)          (reconciler.py)
        |                     |
        +----------+----------+
                   |
                   v
         INVESTIGATION RESULT
                   |
                   v
            GROUNDING LAYER
                   |
                   v
                GROQ LLM
                   |
                   v
         EXPLANATION / CUSTOMER REPLY / Q&A
```

---

## Project Structure

```text
NirNaya/
├── app.py
├── data/
│   ├── generate_data.py
│   ├── gateway.csv
│   ├── bank.csv
│   └── ledger.csv
├── engine/
│   ├── tracer.py
│   └── reconciler.py
├── AI/
│   ├── explainer.py
│   ├── grounding.py
│   └── prompts.py
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
└── test_all_scenarios.py
```

---

## API

### Investigate a transaction

```http
POST /api/investigate
```
```json
{ "transaction_id": "TXN_10021" }
```

Returns settlement, gateway, bank, and ledger status, determination (status / root cause / severity), confidence score, evidence, exceptions, recommended action, and a grounded AI explanation.

### Ask a follow-up question

```http
POST /api/ask
```
```json
{ "transaction_id": "TXN_10021", "question": "Why is this delayed?" }
```

The AI answers using only the verified investigation context for that transaction — it does not have access to raw CSV data directly.

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python + Flask | API and orchestration |
| Data | CSV + Pandas | Mock settlement records |
| Reconciliation | Rule-based engine | Deterministic financial decisions |
| AI | Groq (`openai/gpt-oss-20b`) | Grounded natural-language explanation |
| Frontend | HTML + CSS + JavaScript | Investigation interface |
| Testing | Python (`requests`) | Scenario validation |

The stack is intentionally lightweight so the system can be demonstrated end-to-end without unnecessary infrastructure.

---

## Design Principles

**Evidence before explanation.** The system establishes what happened before asking AI to explain it.

**Deterministic financial decisions.** Amounts, statuses, UTRs, and mismatches are evaluated by code, not the LLM.

**Explicit uncertainty.** If evidence is incomplete or contradictory, NirNaya says so via the `exceptions` field rather than guessing.

**Explainable outputs.** Every conclusion in the AI explanation can be traced back to a specific piece of evidence the backend already verified.

**Actionable support.** The output includes a recommended next action, not just a diagnosis.

---

## Setup

```bash
pip install flask flask-cors pandas python-dotenv groq requests
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=<your key>
```

Run:
```bash
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

---

## Synthetic Data

All transaction records used in this project are synthetic, generated by `data/generate_data.py` for this hackathon, per the problem statement's explicit guidance to self-generate mock data. No real fintech, customer, or financial data is used at any point.

---

## Team

**TEAM: 404:SLEEP NOT FOUND**
**MEMBERS : 1. ADITI JHA
            2. VIDUSHI KESHARWANI
            3. GAURI NANDANA M**

Built for **PS-8 — Settlement Q&A Agent for Fintech Support**.

**NirNaya** — *Evidence-First Settlement Intelligence*
