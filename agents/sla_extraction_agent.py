import re

def simple_sla_extraction(contract_text):
    data = {}

    apr_match = re.search(r'APR\):?\s*([\d.]+)%', contract_text)
    if apr_match:
        data["apr"] = float(apr_match.group(1))

    term_match = re.search(r'period of\s*(\d+)\s*months', contract_text)
    if term_match:
        data["term_months"] = int(term_match.group(1))

    payment_match = re.search(r'Monthly Lease Payment:\s*USD\s*([\d,]+)', contract_text)
    if payment_match:
        data["monthly_payment"] = payment_match.group(1)

    down_match = re.search(r'Down Payment:\s*USD\s*([\d,]+)', contract_text)
    if down_match:
        data["down_payment"] = down_match.group(1)

    mileage_match = re.search(r'Allowed Mileage:\s*([\d,]+)', contract_text)
    if mileage_match:
        data["mileage_per_year"] = mileage_match.group(1)

    return data
