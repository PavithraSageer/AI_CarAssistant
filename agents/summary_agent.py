def generate_response(sla_data, risk_report):
    print("----- Contract Summary -----\n")
    print(f"APR: {sla_data['apr']}%")
    print(f"Lease Term: {sla_data['term_months']} months")
    print(f"Monthly Payment: USD {sla_data['monthly_payment']}")
    print(f"Down Payment: USD {sla_data['down_payment']}")
    print(f"Mileage Per Year: {sla_data['mileage_per_year']} miles\n")

    print("----- Risk Analysis -----\n")
    for risk in risk_report:
        print("-", risk)

