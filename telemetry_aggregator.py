import json
import os
from collections import Counter

def aggregate_telemetry(user_id="user_123"):
    telemetry_path = os.path.join("data", user_id, "telemetry.json")
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
    
    report = {
        "user_id": user_id,
        "total_requests": len(data),
        "total_tokens_consumed": total_tokens,
        "guardrail_incidents": dict(rules_triggered),
        "error_count": len(errors),
        "incident_summary": incident_summary
    }
    
    # Write report to file for Regulator
    report_path = os.path.join("data", user_id, "incident_summary.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"✅ Telemetry aggregated successfully. Report saved to {report_path}.")
    return report

if __name__ == "__main__":
    aggregate_telemetry()
