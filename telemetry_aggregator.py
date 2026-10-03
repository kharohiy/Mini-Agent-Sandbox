import json
import os
import hashlib
import re
from collections import Counter

USER_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


def _evidence_record(index, entry):
    if entry.get("event") == "guardrail_triggered":
        rule = re.sub(r"[^a-z0-9_.:-]+", "_", str(entry.get("rule", "unknown")).lower())
        affected_rule = f"guardrail.{rule}"
        kind = "guardrail_triggered"
    elif "Error" in str(entry.get("status", "")) or entry.get("status") == "ModelProviderExhausted":
        affected_rule = "model.error_handling"
        kind = "model_error"
    else:
        return None
    safe = {
        "kind": kind,
        "affected_rule": affected_rule,
        "timestamp": str(entry.get("timestamp", "")),
        "layer": str(entry.get("layer", "")),
        "status": str(entry.get("status", "")),
    }
    digest = hashlib.sha256(
        (str(index) + json.dumps(safe, sort_keys=True)).encode("utf-8")
    ).hexdigest()[:16]
    return {"id": f"evt-{digest}", **safe}


def aggregate_telemetry(user_id="user_123", base_dir="data"):
    if not isinstance(user_id, str) or not USER_ID.fullmatch(user_id):
        raise ValueError("invalid telemetry user id")
    telemetry_path = os.path.join(base_dir, user_id, "telemetry.json")
    if not os.path.exists(telemetry_path):
        print("{\"error\": \"Telemetry not found\"}")
        return None

    with open(telemetry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Metrics Calculation
    total_tokens = sum(d.get("tokens_used", 0) for d in data)
    guardrail_events = [d for d in data if d.get("event") == "guardrail_triggered"]
    
    # 2. Attack Vectors Analysis
    rules_triggered = Counter(e.get("rule") for e in guardrail_events)
    
    # 3. Error Rates
    errors = [d for d in data if "Error" in d.get("status", "")]
    
    # 4. Generate Incident Summary
    incident_summary = (
        f"Detected {len(guardrail_events)} security events "
        f"and {len(errors)} system errors."
    )
    
    evidence = [item for index, entry in enumerate(data)
                if (item := _evidence_record(index, entry)) is not None]
    report = {
        "user_id": user_id,
        "total_records": len(data),
        "total_tokens_consumed": total_tokens,
        "guardrail_incidents": dict(rules_triggered),
        "error_count": len(errors),
        "incident_summary": incident_summary,
        "evidence": evidence[-50:],
    }
    
    # Write report to file for Regulator
    report_path = os.path.join(base_dir, user_id, "incident_summary.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"✅ Telemetry aggregated successfully. Report saved to {report_path}.")
    return report

if __name__ == "__main__":
    aggregate_telemetry()
