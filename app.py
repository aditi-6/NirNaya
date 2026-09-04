"""
app.py
Flask API for NirNaya.
Exposes /api/trace which returns the deterministic reconciliation result.
AI explanation is plugged in later — for now it returns a placeholder so
frontend can build against a complete response shape.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import math

# Make sure engine/ is importable
sys.path.append(os.path.join(os.path.dirname(__file__), "engine"))

from engine.tracer import trace_transaction
from engine.reconciler import reconcile

app = Flask(__name__)
CORS(app)  # allow frontend (different port) to call this API


def clean_nans(obj):
    """Recursively replace NaN/float-nan with None so the JSON is valid."""
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "NirNaya backend"})


@app.route("/api/investigate", methods=["POST"])
def investigate():
    """
    Same underlying logic as /api/trace, reshaped into the nested
    investigation_result.json contract shape for the AI/frontend layers.
    NOTE: 'timeline' is intentionally omitted for now (not enough time to
    build a reliable event sequence) — do not build against a timeline field.
    """
    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id", "").strip()

    if not transaction_id:
        return jsonify({"error": "transaction_id is required"}), 400

    trace_result = trace_transaction(transaction_id)
    reconciliation = reconcile(trace_result)

    if not trace_result.get("found"):
        return jsonify(clean_nans({
            "transaction_id": transaction_id,
            "amount": None,
            "currency": None,
            "settlement": None,
            "gateway": None,
            "bank": None,
            "ledger": None,
            "determination": {
                "status": "EXCEPTION",
                "root_cause": reconciliation["classification"],
                "severity": reconciliation["severity"]
            },
            "confidence": reconciliation["confidence"],
            "evidence": reconciliation["evidence"],
            "exceptions": reconciliation["exceptions"],
            "recommended_action": reconciliation["recommended_action"]
        }))

    gateway = trace_result["gateway"]
    bank_records = trace_result["bank_records"]
    bank = bank_records[0] if bank_records else None
    ledger = trace_result["ledger"]

    # Map internal classification -> user-facing status
    status_map = {
        "SUCCESS": "SETTLED",
        "BANK_POSTING_DELAY": "PENDING",
        "SETTLEMENT_ON_HOLD": "PENDING",
        "PARTIAL_SETTLEMENT": "PENDING",
        "LEDGER_SYNC_DELAY": "PENDING",
        "BANK_REJECTION": "FAILED",
        "GATEWAY_FAILURE": "FAILED",
    }
    user_status = status_map.get(reconciliation["classification"], "EXCEPTION")

    response = {
        "transaction_id": transaction_id,
        "amount": gateway.get("amount"),
        "currency": gateway.get("currency"),
        "settlement": {
            "settlement_id": gateway.get("settlement_id") or None,
            "status": gateway.get("settlement_status"),
            "utr": gateway.get("utr")
        },
        "gateway": {
            "status": gateway.get("payment_status"),
            "amount": gateway.get("amount"),
            "timestamp": gateway.get("captured_at")
        },
        "bank": {
            "status": bank.get("bank_status") if bank else None,
            "amount": bank.get("amount") if bank else None,
            "utr": bank.get("utr") if bank else None,
            "timestamp": bank.get("credited_at") if bank else None
        } if bank else None,
        "ledger": {
            "status": ledger.get("ledger_status") if ledger else None,
            "amount": ledger.get("net_amount") if ledger else None,
            "timestamp": ledger.get("posted_at") if ledger else None
        } if ledger else None,
        "determination": {
            "status": user_status,
            "root_cause": reconciliation["classification"],
            "severity": reconciliation["severity"]
        },
        "confidence": reconciliation["confidence"],
        "evidence": reconciliation["evidence"],
        "exceptions": reconciliation["exceptions"],
        "recommended_action": reconciliation["recommended_action"]
    }

    return jsonify(clean_nans(response))


@app.route("/api/trace", methods=["POST"])
def trace():
    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id", "").strip()

    if not transaction_id:
        return jsonify({"error": "transaction_id is required"}), 400

    trace_result = trace_transaction(transaction_id)
    reconciliation = reconcile(trace_result)

    # ---- Placeholder AI explanation ----
    # Person 2 (AI) will replace this block by importing their own
    # ai/explainer.py and calling it with `reconciliation` as input.
    # Until that's wired in, we return a clearly-labeled placeholder so
    # the frontend can already build against the final response shape.
    ai_explanation = {
        "summary": f"[AI explanation pending] Classification: {reconciliation['classification']}",
        "explanation": "AI layer not yet connected. This is a placeholder.",
        "customer_reply": None
    }

    response = {
        "transaction_id": transaction_id,
        "found": trace_result.get("found", False),
        "gateway": trace_result.get("gateway"),
        "bank_records": trace_result.get("bank_records"),
        "ledger": trace_result.get("ledger"),
        "classification": reconciliation["classification"],
        "severity": reconciliation["severity"],
        "confidence": reconciliation["confidence"],
        "evidence": reconciliation["evidence"],
        "exceptions": reconciliation["exceptions"],
        "recommended_action": reconciliation["recommended_action"],
        "ai": ai_explanation
    }

    return jsonify(clean_nans(response))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
