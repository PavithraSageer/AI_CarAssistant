from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz
import re
import shutil
import os
import requests
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


@app.get("/")
def home():
    return {"message": "DealGuard Car Contract Analyzer API Running"}


def extract_text_from_pdf(file_path):

    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        text += page.get_text()

    return text


def extract_vin(text):

    vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    matches = re.findall(vin_pattern, text)

    if matches:
        return matches[0]

    return "VIN not found"


def calculate_fairness(text):

    score = 100
    issues = []

    if not re.search(r"Seller Name:", text):
        score -= 15
        issues.append("Missing seller name")

    if not re.search(r"Buyer Name:", text):
        score -= 15
        issues.append("Missing buyer name")

    if not re.search(r"VIN:\s*[A-HJ-NPR-Z0-9]{17}", text):
        score -= 20
        issues.append("Missing or invalid VIN")

    if not re.search(r"Sale Price:", text):
        score -= 15
        issues.append("Sale price missing")

    if not re.search(r"Date:", text):
        score -= 10
        issues.append("Date missing")

    if "Seller Signature" not in text:
        score -= 10
        issues.append("Seller signature missing")

    if "Buyer Signature" not in text:
        score -= 10
        issues.append("Buyer signature missing")

    suspicious_clauses = [
        "sold as-is",
        "no responsibility",
        "buyer assumes all risk"
    ]

    for clause in suspicious_clauses:
        if clause.lower() in text.lower():
            score -= 20
            issues.append("Suspicious clause detected: " + clause)

    if score < 0:
        score = 0

    return score, issues


def risk_level(score):

    if score >= 90:
        return "Low Risk"

    elif score >= 70:
        return "Medium Risk"

    else:
        return "High Risk"


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):

    file_location = f"temp_{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(file_location)

    vin = extract_vin(extracted_text)

    fairness_score, issues = calculate_fairness(extracted_text)

    risk = risk_level(fairness_score)

    os.remove(file_location)

    return JSONResponse(
        content={
            "filename": file.filename,
            "vin": vin,
            "fairness_score": fairness_score,
            "risk_level": risk,
            "issues": issues,
            "extracted_text": extracted_text
        }
    )


@app.get("/vin/{vin_number}")
def vin_lookup(vin_number: str):

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin_number}?format=json"

    response = requests.get(url)
    data = response.json()

    if data["Results"]:
        car = data["Results"][0]

        return {
            "vin": vin_number,
            "make": car.get("Make"),
            "model": car.get("Model"),
            "year": car.get("ModelYear"),
            "body_class": car.get("BodyClass"),
            "engine": car.get("EngineModel"),
            "fuel_type": car.get("FuelTypePrimary")
        }

    return {"error": "VIN not found"}


@app.post("/chat/")
async def chat_assistant(
    message: str = Body(...),
    contract_text: str = Body("")
):

    prompt = f"""
You are DealGuard AI, an assistant that reviews vehicle purchase or lease contracts.

Your tasks:
1. Identify risky or unfair clauses
2. Explain contract terms clearly
3. Suggest negotiation strategies

Contract Text:
{contract_text}

User Question:
{message}

Give short, clear, practical advice.
"""

    try:

        response = model.generate_content(prompt)

        return {"response": response.text}

    except Exception as e:
        return {"response": f"AI error: {str(e)}"}
