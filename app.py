from flask import Flask, request, jsonify
import os

from agents.document_handler_agent import extract_text_from_file
from agents.coordinator_agent import process_contract

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Extract text
    raw_text = extract_text_from_file(file_path)

    # Process contract
    sla_data, validation_issues, risk_report = process_contract(raw_text)

    # Save extracted text (storage layer)
    save_extracted_text(file.filename, raw_text)

    return jsonify({
        "sla_data": sla_data,
        "validation_issues": validation_issues,
        "risk_report": risk_report
    })


def save_extracted_text(filename, text):
    os.makedirs("storage", exist_ok=True)
    with open(f"storage/{filename}.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    app.run(debug=True)

