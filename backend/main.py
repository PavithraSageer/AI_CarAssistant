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

# Updated CORS to be more explicit for Lovable/Render environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter Client Setup
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# In-memory storage (Note: This clears if Render restarts)
contract_memory = {
    "text": ""
}

# --- Pydantic Models for Chat ---
class ChatRequest(BaseModel):
    message: str

# --- Utility Functions ---

def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_vin(text):
    vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    matches = re.findall(vin_pattern, text)
    return matches[0] if matches else "VIN not found"

def calculate_fairness(text):
    score = 100
    issues = []
    
    checks = {
        r"Seller Name:": (15, "Missing seller name"),
        r"Buyer Name:": (15, "Missing buyer name"),
        r"VIN:\s*[A-HJ-NPR-Z0-9]{17}": (20, "Missing or invalid VIN"),
        r"Sale Price:": (15, "Sale price missing"),
        r"Date:": (10, "Date missing")
    }

    for pattern, (penalty, message) in checks.items():
        if not re.search(pattern, text, re.IGNORECASE):
            score -= penalty
            issues.append(message)

    if "Seller Signature" not in text:
        score -= 10
        issues.append("Seller signature missing")
    if "Buyer Signature" not in text:
        score -= 10
        issues.append("Buyer signature missing")

    suspicious_clauses = ["sold as-is", "no responsibility", "buyer assumes all risk"]
    for clause in suspicious_clauses:
        if clause.lower() in text.lower():
            score -= 20
            issues.append(f"Suspicious clause detected: {clause}")

    return max(0, score), issues

def risk_level(score):
    if score >= 90: return "Low Risk"
    if score >= 70: return "Medium Risk"
    return "High Risk"

# --- API Endpoints ---

@app.get("/")
def home():
    return {"status": "online", "message": "DealGuard Car Contract Analyzer API"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_text = extract_text_from_pdf(file_location)
        vin = extract_vin(extracted_text)
        fairness_score, issues = calculate_fairness(extracted_text)
        risk = risk_level(fairness_score)
        
        # Save to memory for the chat assistant
        contract_memory["text"] = extracted_text

        return JSONResponse(content={
            "filename": file.filename,
            "vin": vin,
            "fairness_score": fairness_score,
            "risk_level": risk,
            "issues": issues,
            "extracted_text": extracted_text[:1000] + "..." # Truncated for response clarity
        })
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)

@app.get("/vin/{vin_number}")
def vin_lookup(vin_number: str):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin_number}?format=json"
    response = requests.get(url)
    data = response.json()

    if data.get("Results"):
        car = data["Results"][0]
        return {
            "VIN": vin_number,
            "Make": car.get("Make"),
            "Model": car.get("Model"),
            "Year": car.get("ModelYear"),
            "BodyClass": car.get("BodyClass"),
            "Engine": car.get("EngineModel"),
            "FuelType": car.get("FuelTypePrimary")
        }
    return {"error": "VIN not found"}

@app.post("/chat/")
async def chat_assistant(request: ChatRequest):
    # Using the Pydantic model 'request' ensures JSON compatibility with Lovable
    contract_text = contract_memory.get("text", "No contract uploaded yet.")
    
    prompt = f"""
    You are DealGuard AI, a car contract expert.
    Context: {contract_text[:3000]} 
    User Question: {request.message}
    
    Provide helpful, professional advice. If the info isn't in the text, say so.
    """

    try:
        # Note: Using a more stable free model alternative
        response = client.chat.completions.create(
            model="google/gemma-2-9b-it:free", 
            messages=[
                {"role": "system", "content": "You are a vehicle contract expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        reply = response.choices[0].message.content
        return {"response": reply}

    except Exception as e:
        print(f"OpenRouter Error: {e}")
        return {"response": f"I'm having trouble reaching my brain right now. Error: {str(e)}"}
