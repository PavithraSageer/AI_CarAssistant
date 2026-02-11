"""
Risk Analysis Agent
-------------------
Analyzes extracted SLA data and identifies
potential risks or unfair contract clauses.
"""

def analyze_risk(sla_data):
    print("Risk Analysis Agent running...")

    risks = []

    # Example rule-based checks (can improve later)
    if sla_data.get("apr") and sla_data["apr"] > 8:
        risks.append("High APR detected. This may be above market average.")

    if sla_data.get("mileage_limit") and sla_data["mileage_limit"] < 10000:
        risks.append("Low mileage limit. You may incur overage charges.")

    if sla_data.get("early_termination"):
        risks.append("Early termination clause present. Review penalties carefully.")

    if not risks:
        risks.append("No major risks detected based on current analysis.")

    return risks
