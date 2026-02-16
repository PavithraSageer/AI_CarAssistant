from agents.preprocessing_agent import preprocess_text
from agents.sla_extraction_agent import simple_sla_extraction
from agents.validation_agent import validate_sla_data
from agents.risk_analysis_agent import risk_analysis


def process_contract(raw_text):
    cleaned_text = preprocess_text(raw_text)

    sla_data = simple_sla_extraction(cleaned_text)

    validation_issues = validate_sla_data(sla_data)

    risk_report = risk_analysis(sla_data)

    return sla_data, validation_issues, risk_report
