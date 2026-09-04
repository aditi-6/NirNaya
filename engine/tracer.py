"""
engine/tracer.py
Loads the 3 CSVs and finds the matching rows for a given transaction ID.
This is the "search" layer — no decision-making happens here.
"""

import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Load once at import time (fast enough for hackathon scale)
gateway_df = pd.read_csv(os.path.join(DATA_DIR, "gateway.csv"), dtype=str)
bank_df = pd.read_csv(os.path.join(DATA_DIR, "bank.csv"), dtype=str)
ledger_df = pd.read_csv(os.path.join(DATA_DIR, "ledger.csv"), dtype=str)

# Convert numeric columns back to numbers (dtype=str keeps IDs/UTRs safe from
# pandas turning them into floats, but amounts need to be numeric)
for col in ["amount", "settlement_amount", "fees", "tax"]:
    if col in gateway_df.columns:
        gateway_df[col] = pd.to_numeric(gateway_df[col], errors="coerce")

for col in ["amount"]:
    if col in bank_df.columns:
        bank_df[col] = pd.to_numeric(bank_df[col], errors="coerce")

for col in ["debit", "credit", "net_amount"]:
    if col in ledger_df.columns:
        ledger_df[col] = pd.to_numeric(ledger_df[col], errors="coerce")


def find_gateway(transaction_id):
    row = gateway_df[gateway_df["transaction_id"] == transaction_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def find_bank_records(transaction_id):
    """Returns a LIST because duplicate bank entries are a valid scenario."""
    rows = bank_df[bank_df["transaction_id"] == transaction_id]
    return rows.to_dict(orient="records")  # empty list if none found


def find_ledger(transaction_id):
    row = ledger_df[ledger_df["transaction_id"] == transaction_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def trace_transaction(transaction_id):
    """
    Main entry point. Given a transaction_id, pulls the full picture
    across gateway, bank, and ledger.
    """
    gateway = find_gateway(transaction_id)

    if gateway is None:
        return {
            "transaction_id": transaction_id,
            "found": False,
            "error": "No transaction found with this ID in gateway records."
        }

    bank_records = find_bank_records(transaction_id)
    ledger = find_ledger(transaction_id)

    return {
        "transaction_id": transaction_id,
        "found": True,
        "gateway": gateway,
        "bank_records": bank_records,   # list — could be 0, 1, or 2+ rows
        "ledger": ledger,               # dict or None
    }


if __name__ == "__main__":
    # quick manual test
    import json
    result = trace_transaction("TXN_10021")  # bank delay scenario
    print(json.dumps(result, indent=2, default=str))
