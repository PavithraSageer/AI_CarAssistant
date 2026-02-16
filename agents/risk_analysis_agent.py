def risk_analysis(sla_data):
    risks = []

    if sla_data.get("apr") and sla_data["apr"] > 8:
        risks.append("High APR detected.")

    if sla_data.get("mileage_per_year"):
        mileage = int(sla_data["mileage_per_year"].replace(",", ""))
        if mileage < 10000:
            risks.append("Low mileage limit. Possible overage charges.")

    if not risks:
        risks.append("No major financial risks detected.")

    return risks
