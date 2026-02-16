from PyPDF2 import PdfReader
from agents.coordinator_agent import process_contract
from agents.summary_agent import generate_response


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def main():
    pdf_path = "chevrolet.pdf"

    raw_text = extract_text_from_pdf(pdf_path)

    sla_data, validation_issues, risk_report = process_contract(raw_text)

    if validation_issues:
        print("Validation Issues:", validation_issues)

    generate_response(sla_data, risk_report)


if __name__ == "__main__":
    main()
