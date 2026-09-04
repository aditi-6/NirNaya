"""
engine/reconciler.py
Pure rule-based logic. NO AI here. This is what you point to when a judge
asks "how do you avoid hallucination?" -> "financial state is decided by
code, not the LLM."
"""


def reconcile(trace_result):
    """
    Takes the dict returned by tracer.trace_transaction() and returns:
    {
        "classification": str,
        "severity": "LOW" | "MEDIUM" | "HIGH",
        "confidence": int (0-100),
        "evidence": [str, ...],
        "exceptions": [str, ...],
        "recommended_action": str
    }
    """
    if not trace_result.get("found"):
        return {
            "classification": "TRANSACTION_NOT_FOUND",
            "severity": "HIGH",
            "confidence": 100,
            "evidence": [],
            "exceptions": ["No gateway record exists for this transaction ID."],
            "recommended_action": "Verify the transaction ID with the merchant and check for typos."
        }

    gateway = trace_result["gateway"]
    bank_records = trace_result["bank_records"]
    ledger = trace_result["ledger"]

    evidence = []
    exceptions = []
    confidence = 0

    gw_payment_status = str(gateway.get("payment_status", "")).lower()
    gw_settlement_status = str(gateway.get("settlement_status", "")).lower()
    gw_settlement_amount = gateway.get("settlement_amount")
    gw_utr = gateway.get("utr")

    # ---- Gateway checks ----
    if gw_payment_status:
        evidence.append(f"Gateway payment status: {gw_payment_status}")
        confidence += 20

    # 1. Gateway itself failed -> nothing else matters
    if gw_payment_status == "failed":
        exceptions_note = gateway.get("failure_reason", "")
        return {
            "classification": "GATEWAY_FAILURE",
            "severity": "HIGH",
            "confidence": 95,
            "evidence": evidence,
            "exceptions": [f"Gateway reported failure: {exceptions_note}"] if exceptions_note else [],
            "recommended_action": "No settlement was ever initiated. Direct merchant to retry payment; no bank/ledger action needed."
        }

    # 2. Settlement on hold
    if gw_settlement_status == "on_hold":
        evidence.append("Settlement status: on_hold (risk review)")
        confidence += 20
        return {
            "classification": "SETTLEMENT_ON_HOLD",
            "severity": "MEDIUM",
            "confidence": 85,
            "evidence": evidence,
            "exceptions": ["Settlement has not been released by the gateway; no bank transfer was initiated."],
            "recommended_action": "Escalate to risk/compliance team to review hold reason. No bank-side action possible yet."
        }

    # ---- Bank checks ----
    if not bank_records:
        exceptions.append("No corresponding bank record was found for this settlement.")
        return {
            "classification": "MISSING_BANK_RECORD",
            "severity": "HIGH",
            "confidence": 60,
            "evidence": evidence,
            "exceptions": exceptions,
            "recommended_action": "Check with banking partner directly using the settlement ID; bank record may be delayed in ingestion."
        }

    if len(bank_records) > 1:
        exceptions.append(f"Found {len(bank_records)} bank records for a single settlement (expected 1).")
        confidence += 10

    bank = bank_records[0]
    bank_status = str(bank.get("bank_status", "")).lower()
    bank_amount = bank.get("amount")
    bank_utr = bank.get("utr")

    evidence.append(f"Bank status: {bank_status}")
    confidence += 20

    # UTR check
    if gw_utr and bank_utr and str(gw_utr) != str(bank_utr):
        exceptions.append(f"UTR mismatch: gateway has '{gw_utr}', bank record has '{bank_utr}'.")
    else:
        evidence.append("UTR matched between gateway and bank record.")
        confidence += 15

    # Amount check (only meaningful if bank credited/partial, not for pending/rejected)
    amount_mismatch = False
    if bank_status in ("credited", "partial") and gw_settlement_amount is not None and bank_amount is not None:
        try:
            if abs(float(gw_settlement_amount) - float(bank_amount)) > 1:  # >1 rupee tolerance
                amount_mismatch = True
        except (TypeError, ValueError):
            pass

    if bank_status in ("credited",) and not amount_mismatch:
        evidence.append("Bank amount matches gateway settlement amount.")
        confidence += 15

    duplicate_flag = len(bank_records) > 1

    # ---- Ledger checks ----
    if ledger is None:
        exceptions.append("Ledger entry is unavailable for this transaction.")
    else:
        ledger_status = str(ledger.get("ledger_status", "")).lower()
        evidence.append(f"Ledger status: {ledger_status}")
        confidence += 10

    # ---- Now classify based on combined picture ----

    if duplicate_flag:
        return {
            "classification": "DUPLICATE_BANK_ENTRY",
            "severity": "HIGH",
            "confidence": min(confidence, 100),
            "evidence": evidence,
            "exceptions": exceptions,
            "recommended_action": "Flag to banking ops for manual de-duplication before confirming settlement to merchant."
        }

    if exceptions and any("UTR mismatch" in e for e in exceptions):
        return {
            "classification": "UTR_MISMATCH",
            "severity": "HIGH",
            "confidence": max(confidence - 30, 30),
            "evidence": evidence,
            "exceptions": exceptions,
            "recommended_action": "Do not confirm settlement to merchant. Escalate to banking partner to verify correct UTR."
        }

    if bank_status == "rejected":
        reason = bank.get("bank_response_message", "unspecified reason")
        return {
            "classification": "BANK_REJECTION",
            "severity": "HIGH",
            "confidence": min(confidence, 95),
            "evidence": evidence,
            "exceptions": [f"Bank rejected transfer: {reason}"],
            "recommended_action": "Verify merchant's bank account details are current. Merchant may need to re-submit valid account info."
        }

    if bank_status == "pending":
        return {
            "classification": "BANK_POSTING_DELAY",
            "severity": "LOW",
            "confidence": min(confidence, 90),
            "evidence": evidence,
            "exceptions": exceptions or ["Bank has not yet confirmed credit; this may resolve within the normal posting window."],
            "recommended_action": "Wait for standard bank SLA window. If not credited after SLA, escalate with UTR to banking ops."
        }

    if bank_status == "partial":
        return {
            "classification": "PARTIAL_SETTLEMENT",
            "severity": "MEDIUM",
            "confidence": min(confidence, 90),
            "evidence": evidence,
            "exceptions": [f"Only ₹{bank_amount} settled out of expected ₹{gw_settlement_amount}."],
            "recommended_action": "Remaining balance should settle in a subsequent cycle once available balance permits. Monitor next settlement run."
        }

    if amount_mismatch:
        return {
            "classification": "AMOUNT_MISMATCH",
            "severity": "HIGH",
            "confidence": max(confidence - 20, 40),
            "evidence": evidence,
            "exceptions": [f"Gateway settlement amount (₹{gw_settlement_amount}) does not match bank credited amount (₹{bank_amount})."],
            "recommended_action": "Do not close ticket. Escalate to reconciliation team for manual amount verification."
        }

    if ledger is None:
        return {
            "classification": "MISSING_LEDGER_RECORD",
            "severity": "MEDIUM",
            "confidence": min(confidence, 75),
            "evidence": evidence,
            "exceptions": exceptions,
            "recommended_action": "Bank has credited funds correctly; internal ledger ingestion needs investigation."
        }

    ledger_status = str(ledger.get("ledger_status", "")).lower()
    if ledger_status == "pending" and bank_status == "credited":
        return {
            "classification": "LEDGER_SYNC_DELAY",
            "severity": "LOW",
            "confidence": min(confidence, 85),
            "evidence": evidence,
            "exceptions": ["Bank has credited the amount but internal ledger has not yet synced."],
            "recommended_action": "No merchant-facing issue. Internal ledger sync job should catch up; monitor if delay exceeds a few hours."
        }

    if bank_status == "credited" and ledger_status == "posted" and not amount_mismatch:
        return {
            "classification": "SUCCESS",
            "severity": "LOW",
            "confidence": min(confidence, 100),
            "evidence": evidence,
            "exceptions": [],
            "recommended_action": "No action needed. Settlement completed successfully end-to-end."
        }

    # Fallback — genuinely unclear
    return {
        "classification": "INSUFFICIENT_EVIDENCE",
        "severity": "MEDIUM",
        "confidence": max(confidence - 40, 20),
        "evidence": evidence,
        "exceptions": exceptions + ["Combination of records does not match a known pattern confidently."],
        "recommended_action": "Manual review recommended before responding to merchant."
    }


if __name__ == "__main__":
    from tracer import trace_transaction
    import json

    test_ids = ["TXN_10001", "TXN_10021", "TXN_10029", "TXN_10033",
                "TXN_10037", "TXN_10041", "TXN_10045", "TXN_10049",
                "TXN_10052", "TXN_10055", "TXN_10058", "TXN_10060"]

    for tid in test_ids:
        trace = trace_transaction(tid)
        result = reconcile(trace)
        print(f"{tid:12s} -> {result['classification']:25s} (confidence {result['confidence']})")
