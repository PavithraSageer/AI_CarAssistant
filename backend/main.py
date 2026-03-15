from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fitz  # PyMuPDF
import re
import shutil
import os
import requests
from openai import OpenAI

app = FastAPI()

# Allow Lovable to connect to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Shared memory for the session
contract_memory = {"text": ""}

class ChatRequest(BaseModel):
    message: str

# --- Helper Functions for Extraction ---

def extract_vin(text):
    # Improved regex to find VINs even if there are weird spaces or labels
    vin_pattern = r'[A-HJ-NPR-Z0-9]{17}'
    matches = re.findall(vin_pattern, text.replace(" ", ""))
    return matches[0] if matches else "VIN not found"

def calculate_fairness(text):
    score = 100
    issues = []
    
    # Case-insensitive checks for common contract requirements
    requirements = {
        "Seller": r"(Seller|Dealer|Vendor)",
        "Buyer": r"(Buyer|Purchaser|Customer)",
        "Price": r"(Price|Amount|Total|Purchase Price)",
        "Date": r"(Date|Executed on)",
        "Signature": r"(Signature|Signed)"
    }

    for label, pattern in requirements.items():
        if not re.search(pattern, text, re.IGNORECASE):
            score -= 15
            issues.append(f"Missing {label} information or signature block.")

    suspicious = ["as-is", "no warranty", "waive all rights", "non-refundable"]
    for word in suspicious:
        if word.lower() in text.lower():
            score -= 10
            issues.append(f"Caution: '{word}' clause detected.")

    return max(0, score), issues

# --- API Endpoints ---

@app.get("/")
def home():
    return {"message": "DealGuard API is Live"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc = fitz.open(file_location)
        extracted_text = ""
        for page in doc:
            extracted_text += page.get_text()
        
        # Save to memory
        contract_memory["text"] = extracted_text
        
        vin = extract_vin(extracted_text)
        fairness_score, issues = calculate_fairness(extracted_text)
        
        risk = "Low Risk" if fairness_score >= 85 else "Medium Risk" if fairness_score >= 60 else "High Risk"

        return {
            "vin": vin,
            "fairness_score": fairness_score,
            "risk_level": risk,
            "issues": issues,
            "extracted_text": extracted_text[:2000] # Send sample to frontend
        }
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)

@app.get("/vin/{vin_number}")
def vin_lookup(vin_number: str):
    if vin_number == "VIN not found":
        return {"error": "No VIN provided"}
        
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin_number}?format=json"
    response = requests.get(url)
    data = response.json()

    if data.get("Results"):
        car = data["Results"][0]
        return {
            "Make": car.get("Make"),
            "Model": car.get("Model"),
            "Year": car.get("ModelYear"),
            "Body": car.get("BodyClass"),
            "Engine": car.get("EngineModel"),
            "Fuel": car.get("FuelTypePrimary")
        }
    return {"error": "Vehicle details not found"}

@app.post("/chat/")
async def chat_assistant(request: ChatRequest):
    # List of models to try if "Limit Exceeded" happens
    models = ["openrouter/free", "meta-llama/llama-3.3-70b-instruct:free", "mistralai/mistral-small-3.1-24b-instruct:free"]
    
    for model_id in models:
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are DealGuard AI, a professional car contract legal assistant."},
                    {"role": "user", "content": f"Context: {contract_memory['text'][:3500]}\n\nQuestion: {request.message}"}
                ],
                timeout=20
            )
            return {"response": response.choices[0].message.content}
        except Exception:
            continue # Try next model
            
    return {"response": "All AI lanes are full. Please try again in 30 seconds."}
