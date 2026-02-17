# AI-Based Car Lease Contract Review and Negotiation Assistant

## 📌 Project Overview

This project is a backend multi-agent system designed to analyze car lease and loan agreements. 

The system accepts different document formats (PDF, scanned PDF, image files), extracts contract text using OCR when required, and processes the content using modular AI agents.

---

## 🧠 System Architecture

The system follows a modular multi-agent architecture:

- Document Handler Agent – Detects file type and extracts text (PDF or OCR fallback)
- Preprocessing Agent – Cleans and normalizes extracted text
- SLA Extraction Agent – Extracts financial terms (APR, lease term, payments, mileage)
- Validation Agent – Checks required SLA fields
- Risk Analysis Agent – Performs rule-based financial risk analysis
- Summary Agent – Generates structured output
- Coordinator Agent – Orchestrates the complete pipeline

---

## 📂 Project Structure

AI_CarAssistant/
├── agents/
├── docs/
├── main.py
├── requirements.txt
└── LICENSE


---

## ⚙️ Installation

Install dependencies:
pip install -r requirements.txt


---

## ▶️ How to Run

Place a lease document (PDF or image) in the root folder.

Then run:
python main.py


The system will:

1. Detect document type
2. Extract text
3. Process SLA data
4. Perform validation
5. Generate risk analysis summary

---

## 🚀 Milestone 1 Status

- OCR Integration Completed
- Flexible Document Handling Implemented
- Multi-Agent Backend Pipeline Functional
- SLA Extraction and Risk Analysis Working

---

## 📎 Future Enhancements

- VIN API Integration
- LLM-based SLA Extraction
- Market Price Comparison
- Interactive Chatbot Interface
