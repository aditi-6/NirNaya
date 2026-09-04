"""
SettleIQ - Mock Data Generator
Generates gateway.csv, bank.csv, ledger.csv from one canonical transaction list.
Every scenario is deliberate and internally consistent across all 3 files.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

OUT_DIR = "."

# ---------------------------------------------------------
# Scenario definitions
# Each scenario controls how gateway/bank/ledger records look
# ---------------------------------------------------------
SCENARIOS = [
    ("SUCCESS", 20),                 # everything matches, fully settled
    ("BANK_POSTING_DELAY", 8),       # gateway processed, bank pending
    ("BANK_REJECTION", 4),           # bank rejected transfer
    ("GATEWAY_FAILURE", 4),          # gateway itself failed, nothing downstream
    ("SETTLEMENT_ON_HOLD", 4),       # gateway put settlement on hold (risk review)
    ("PARTIAL_SETTLEMENT", 4),       # only part of amount settled
    ("LEDGER_SYNC_DELAY", 4),        # bank credited, ledger not yet posted
    ("AMOUNT_MISMATCH", 3),          # bank credited different amount than gateway
    ("MISSING_BANK_RECORD", 3),      # gateway processed, bank record absent entirely
    ("MISSING_LEDGER_RECORD", 3),    # settled fine but ledger entry missing
    ("UTR_MISMATCH", 2),             # bank record exists but UTR doesn't match settlement UTR
    ("DUPLICATE_BANK_ENTRY", 2),     # two bank credits for same settlement (anomaly)
]

BANKS = ["AXIS", "HDFC", "ICICI", "SBI", "KOTAK"]
FAILURE_REASONS = {
    "GATEWAY_FAILURE": ["INSUFFICIENT_FUNDS", "CARD_DECLINED", "BANK_TIMEOUT", "RISK_BLOCK"],
    "BANK_REJECTION": ["INVALID_ACCOUNT", "ACCOUNT_CLOSED", "IFSC_MISMATCH", "KYC_HOLD"],
}

gateway_rows = []
bank_rows = []
ledger_rows = []

txn_counter = 10000
base_time = datetime(2026, 8, 1, 9, 0, 0)

def next_txn_id():
    global txn_counter
    txn_counter += 1
    return f"TXN_{txn_counter}"

def money(base):
    return round(base + random.uniform(-500, 5000), 2)

row_idx = 0
for scenario, count in SCENARIOS:
    for _ in range(count):
        row_idx += 1
        txn_id = next_txn_id()
        merchant_id = f"MERCH_{random.randint(100,120)}"
        order_id = f"ORDER_{txn_id[-5:]}"
        amount = money(10000)
        currency = "INR"
        captured_at = base_time + timedelta(hours=row_idx * 3, minutes=random.randint(0,59))
        gateway_payment_id = f"PAY_{txn_id[-5:]}"
        settlement_id = f"SET_{70000 + row_idx}"
        utr = f"{random.choice(BANKS)}{random.randint(100000,999999)}"
        bank_account_id = f"ACC_{merchant_id[-3:]}"
        fees = round(amount * 0.02, 2)
        tax = round(fees * 0.18, 2)
        settlement_amount = round(amount - fees - tax, 2)

        # Defaults (SUCCESS case)
        gw_status = "processed"
        gw_settlement_status = "processed"
        gw_failure_code = ""
        gw_failure_reason = ""

        bank_exists = True
        bank_status = "credited"
        bank_amount = settlement_amount
        bank_utr = utr
        bank_initiated_at = captured_at + timedelta(minutes=5)
        bank_credited_at = captured_at + timedelta(hours=2)
        bank_response_code = "00"
        bank_response_message = "SUCCESS"
        duplicate_bank_row = None

        ledger_exists = True
        ledger_status = "posted"
        ledger_net_amount = settlement_amount
        ledger_posted_at = bank_credited_at + timedelta(minutes=10)

        # ---- apply scenario overrides ----
        if scenario == "BANK_POSTING_DELAY":
            bank_status = "pending"
            bank_credited_at = None
            ledger_status = "pending"
            ledger_posted_at = None

        elif scenario == "BANK_REJECTION":
            bank_status = "rejected"
            bank_credited_at = None
            bank_response_code = "R01"
            bank_response_message = random.choice(FAILURE_REASONS["BANK_REJECTION"])
            ledger_status = "pending"
            ledger_posted_at = None

        elif scenario == "GATEWAY_FAILURE":
            gw_status = "failed"
            gw_settlement_status = "not_initiated"
            gw_failure_code = "GTW_ERR"
            gw_failure_reason = random.choice(FAILURE_REASONS["GATEWAY_FAILURE"])
            settlement_id = ""  # never created
            bank_exists = False
            ledger_exists = False

        elif scenario == "SETTLEMENT_ON_HOLD":
            gw_settlement_status = "on_hold"
            bank_exists = False
            ledger_status = "pending"
            ledger_posted_at = None
            ledger_net_amount = 0

        elif scenario == "PARTIAL_SETTLEMENT":
            bank_status = "partial"
            partial_amount = round(settlement_amount * random.uniform(0.4, 0.75), 2)
            bank_amount = partial_amount
            ledger_status = "partial"
            ledger_net_amount = partial_amount

        elif scenario == "LEDGER_SYNC_DELAY":
            ledger_status = "pending"
            ledger_posted_at = None

        elif scenario == "AMOUNT_MISMATCH":
            bank_amount = round(settlement_amount - random.uniform(200, 800), 2)

        elif scenario == "MISSING_BANK_RECORD":
            bank_exists = False
            ledger_status = "pending"
            ledger_posted_at = None

        elif scenario == "MISSING_LEDGER_RECORD":
            ledger_exists = False

        elif scenario == "UTR_MISMATCH":
            bank_utr = f"{random.choice(BANKS)}{random.randint(100000,999999)}"  # deliberately different

        elif scenario == "DUPLICATE_BANK_ENTRY":
            duplicate_bank_row = True

        # ---- write gateway row ----
        gateway_rows.append({
            "transaction_id": txn_id,
            "merchant_id": merchant_id,
            "gateway_payment_id": gateway_payment_id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "payment_status": gw_status,
            "captured_at": captured_at.isoformat(),
            "settlement_id": settlement_id,
            "settlement_status": gw_settlement_status,
            "settlement_amount": settlement_amount if settlement_id else "",
            "fees": fees if settlement_id else "",
            "tax": tax if settlement_id else "",
            "utr": utr if settlement_id else "",
            "settlement_created_at": (captured_at + timedelta(minutes=2)).isoformat() if settlement_id else "",
            "failure_code": gw_failure_code,
            "failure_reason": gw_failure_reason,
            "scenario_tag": scenario,  # remove/ignore in prod — helpful for your own testing
        })

        # ---- write bank row(s) ----
        if bank_exists:
            bank_rows.append({
                "bank_transaction_id": f"BTX_{70000+row_idx}",
                "utr": bank_utr,
                "settlement_id": settlement_id,
                "transaction_id": txn_id,
                "account_id": bank_account_id,
                "amount": bank_amount,
                "currency": currency,
                "bank_status": bank_status,
                "initiated_at": bank_initiated_at.isoformat(),
                "credited_at": bank_credited_at.isoformat() if bank_credited_at else "",
                "bank_response_code": bank_response_code,
                "bank_response_message": bank_response_message,
            })
            if duplicate_bank_row:
                bank_rows.append({
                    "bank_transaction_id": f"BTX_{70000+row_idx}_DUP",
                    "utr": bank_utr,
                    "settlement_id": settlement_id,
                    "transaction_id": txn_id,
                    "account_id": bank_account_id,
                    "amount": bank_amount,
                    "currency": currency,
                    "bank_status": "credited",
                    "initiated_at": (bank_initiated_at + timedelta(minutes=30)).isoformat(),
                    "credited_at": (bank_credited_at + timedelta(minutes=35)).isoformat(),
                    "bank_response_code": "00",
                    "bank_response_message": "SUCCESS",
                })

        # ---- write ledger row ----
        if ledger_exists:
            ledger_rows.append({
                "ledger_entry_id": f"LDG_{70000+row_idx}",
                "transaction_id": txn_id,
                "settlement_id": settlement_id,
                "merchant_id": merchant_id,
                "debit": 0,
                "credit": ledger_net_amount,
                "net_amount": ledger_net_amount,
                "currency": currency,
                "ledger_status": ledger_status,
                "posted_at": ledger_posted_at.isoformat() if ledger_posted_at else "",
                "reference": settlement_id,
            })

# ---------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------
def write_csv(filename, rows):
    if not rows:
        return
    keys = rows[0].keys()
    with open(f"{OUT_DIR}/{filename}", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

write_csv("gateway.csv", gateway_rows)
write_csv("bank.csv", bank_rows)
write_csv("ledger.csv", ledger_rows)

print(f"Generated {len(gateway_rows)} gateway rows, {len(bank_rows)} bank rows, {len(ledger_rows)} ledger rows")
print("Files: gateway.csv, bank.csv, ledger.csv")

# Print one sample TXN ID per scenario so you can test immediately
print("\n--- Sample transaction IDs per scenario (for testing) ---")
seen = set()
for row in gateway_rows:
    tag = row["scenario_tag"]
    if tag not in seen:
        seen.add(tag)
        print(f"{tag:25s} -> {row['transaction_id']}")
