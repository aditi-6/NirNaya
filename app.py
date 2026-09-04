"""
app.py
Flask API for NirNaya.

Endpoints:
- POST /api/investigate  -> nested contract shape (settlement/gateway/bank/ledger/determination) + AI explanation
- POST /api/trace        -> flat shape (for frontend teammate's original contract) + AI explanation
- POST /api/ask          -> follow-up Q&A on a specific transaction, grounded in the same investigation data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import math

sys.path.append(os.path.join(os.path.dirname(__file__), "engine"))

from engine.tracer import trace_transaction
from engine.reconciler import reconcile
from AI.explainer import explain_investigation

app = Flask(__name__)
CORS(app)


def clean_nans(obj):
    """Recursively replace NaN/float-nan with None so the JSON is valid."""
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


def build_investigation_result(transaction_id):
    """
    The ONE place that builds the nested investigation_result.json shape.
    Every endpoint (investigate, trace, ask) should reuse this instead of
    reimplementing the field-mapping logic — that's what caused the bug
    where /api/ask pulled amount/gateway/bank/ledger from reconcile()
    (which never contained them) and got None for everything.
    """
    trace_result = trace_transaction(transaction_id)
    reconciliation = reconcile(trace_result)

    if not trace_result.get("found"):
        return {
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
        }

    gateway = trace_result["gateway"]
    bank_records = trace_result["bank_records"]
    bank = bank_records[0] if bank_records else None
    ledger = trace_result["ledger"]

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

    return {
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


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "NirNaya backend"})


@app.route("/api/investigate", methods=["POST"])
def investigate():
    """
    Nested contract shape for AI/frontend, per investigation_result.json.
    NOTE: 'timeline' is intentionally omitted (not enough time to build a
    reliable event sequence) — don't build against a timeline field.
    """
    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id", "").strip()
    question = data.get("question")

    if not transaction_id:
        return jsonify({"error": "transaction_id is required"}), 400

    result = build_investigation_result(transaction_id)
    result["ai"] = explain_investigation(clean_nans(result), question)

    return jsonify(clean_nans(result))


@app.route("/api/trace", methods=["POST"])
def trace():
    """Flat shape — kept for the frontend teammate's original contract."""
    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id", "").strip()

    if not transaction_id:
        return jsonify({"error": "transaction_id is required"}), 400

    trace_result = trace_transaction(transaction_id)
    reconciliation = reconcile(trace_result)

    # Reuse the same nested builder just to feed the AI consistently
    nested_for_ai = build_investigation_result(transaction_id)
    ai_explanation = explain_investigation(clean_nans(nested_for_ai))

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


@app.route("/api/ask", methods=["POST"])
def ask():
    """Follow-up Q&A about a specific transaction, grounded in its investigation result."""
    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id")
    question = data.get("question")

    if not transaction_id or not question:
        return jsonify({"error": "transaction_id and question are required"}), 400

    try:
        investigation_result = build_investigation_result(transaction_id)

        if investigation_result["determination"]["root_cause"] == "TRANSACTION_NOT_FOUND":
            return jsonify({"error": "Transaction not found"}), 404

        ai_response = explain_investigation(clean_nans(investigation_result), question)

        if not ai_response.get("follow_up_answer"):
            ai_response["follow_up_answer"] = ai_response.get("explanation")

        return jsonify(ai_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
