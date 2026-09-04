"""
test_all_scenarios.py
Run this from C:\\NirNaya (same place as app.py) while app.py is running
in another terminal. Tests all 13 required transaction IDs against
/api/investigate and reports pass/fail for the structural checks.

Usage:
    python test_all_scenarios.py
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

TEST_IDS = [
    "TXN_10001", "TXN_10021", "TXN_10029", "TXN_10033",
    "TXN_10037", "TXN_10041", "TXN_10045", "TXN_10049",
    "TXN_10052", "TXN_10055", "TXN_10058", "TXN_10060",
    "TXN_99999",
]

REQUIRED_TOP_KEYS = [
    "transaction_id", "amount", "currency", "settlement", "gateway",
    "bank", "ledger", "determination", "confidence", "evidence",
    "exceptions", "recommended_action"
]

REQUIRED_DETERMINATION_KEYS = ["status", "root_cause", "severity"]


def check_response(txn_id, data):
    problems = []

    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            problems.append(f"missing top-level key: {key}")

    det = data.get("determination", {})
    for key in REQUIRED_DETERMINATION_KEYS:
        if key not in det:
            problems.append(f"missing determination.{key}")

    # NaN check — NaN would break JSON, so if requests parsed it fine we're
    # okay, but double check no literal 'NaN' string leaked through
    raw = json.dumps(data)
    if "NaN" in raw:
        problems.append("raw response contains literal NaN (invalid JSON)")

    return problems


def main():
    print(f"Testing {len(TEST_IDS)} transaction IDs against {BASE_URL}/api/investigate\n")
    all_passed = True

    for txn_id in TEST_IDS:
        try:
            resp = requests.post(
                f"{BASE_URL}/api/investigate",
                json={"transaction_id": txn_id},
                timeout=30
            )
        except requests.exceptions.ConnectionError:
            print(f"{txn_id:12s} -> FAILED (cannot connect — is app.py running?)")
            all_passed = False
            continue

        if resp.status_code != 200:
            print(f"{txn_id:12s} -> FAILED (HTTP {resp.status_code}): {resp.text[:150]}")
            all_passed = False
            continue

        data = resp.json()
        problems = check_response(txn_id, data)

        det = data.get("determination", {})
        status_line = f"{det.get('status', '?'):10s} / {det.get('root_cause', '?')}"

        if problems:
            print(f"{txn_id:12s} -> ISSUES: {status_line}")
            for p in problems:
                print(f"              - {p}")
            all_passed = False
        else:
            print(f"{txn_id:12s} -> OK: {status_line} (confidence {data.get('confidence')})")

    print()
    if all_passed:
        print("ALL 13 TRANSACTION IDS PASSED ✅")
    else:
        print("SOME TESTS FAILED — see above ❌")


if __name__ == "__main__":
    main()
