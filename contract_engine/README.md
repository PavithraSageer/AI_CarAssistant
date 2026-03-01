# Contract Analysis Engine (FastAPI + OCR + SLA + VIN)

This project provides:

- Contract upload (`PDF`/image) and text extraction without system OCR binaries
- SLA extraction using OpenRouter LLM API
- VIN vehicle lookup using NHTSA API

## 1) Prerequisites

- Python 3.12
- OpenRouter API key (for OCR on images/scanned PDFs and SLA extraction)

## 2) Project setup

```powershell
cd "c:\Users\admin\Desktop\Car Lease\contract_engine"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3) Configure keys

- This project now loads configuration from a dedicated `.env` file using `python-dotenv`.
- Edit `.env` and set at least:
  - `OPENROUTER_API_KEY=YOUR_REAL_KEY`
  - `OPENROUTER_VISION_MODEL=openai/gpt-4o-mini` (optional override for OCR model)
  - `DATABASE_URL=sqlite:///./contract_engine.db` (or PostgreSQL URL)

You can copy `.env.example` to `.env` if you want a clean template first.

## 4) Run server

```powershell
uvicorn main:app --reload
```

Alternative (now supported):

```powershell
python main.py --reload
```

Note: `python main.py "Test.pdf"` does not process the PDF directly. It starts the API and you should upload the file using `POST /upload-contract`.

API docs:

- Swagger UI: http://127.0.0.1:8000/docs

## 5) Example curl tests

### Upload contract (PDF/image)

```bash
curl -X POST "http://127.0.0.1:8000/upload-contract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_contract.pdf"
```

### Extract SLA by document ID

```bash
curl -X POST "http://127.0.0.1:8000/extract-sla/1" \
  -H "accept: application/json"
```

### Get vehicle details by VIN

```bash
curl -X GET "http://127.0.0.1:8000/vehicle-details/1HGCM82633A004352" \
  -H "accept: application/json"
```

## 6) API summary

- `POST /upload-contract`
  - Accepts PDF or image
  - Extracts embedded PDF text first
  - Falls back to OpenRouter vision OCR for scanned PDFs/images
  - Stores `filename`, `extracted_text`, `upload_timestamp`

- `POST /extract-sla/{document_id}`
  - Reads OCR text from DB
  - Calls OpenRouter and enforces strict JSON fields
  - Stores SLA JSON

- `GET /vehicle-details/{vin}`
  - Calls NHTSA VIN decode API
  - Returns `make`, `model`, `model_year`, `recalls`
