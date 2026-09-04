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
