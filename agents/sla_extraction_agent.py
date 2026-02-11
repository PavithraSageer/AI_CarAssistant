"""
SLA Extraction Agent
--------------------
This agent extracts key financial clauses from
a car lease or loan contract.

Responsibilities:
- Extract APR / Interest rate
- Extract Lease/Loan term
- Extract Monthly payment
- Extract Down payment
- Extract Mileage allowance
- Extract Penalties
- Extract Early termination clause
"""

def extract_sla(contract_text):
    print("SLA Extraction Agent running...")

    # Placeholder logic (LLM integration will be added later)
    extracted_data = {
        "apr": None,
        "term": None,
        "monthly_payment": None,
        "down_payment": None,
        "mileage_limit": None,
        "penalties": None,
        "early_termination": None
    }

    return extracted_data


# Example test run (for development purpose)
if __name__ == "__main__":
    sample_text = "This lease has an APR of 7.5% for 36 months with monthly payment of 25000."
    result = extract_sla(sample_text)
    print(result)
