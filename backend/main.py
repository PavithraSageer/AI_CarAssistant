from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fitz 
import re
import shutil
import os
import requests
from openai import OpenAI

app = FastAPI()

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

contract_memory = {"text": ""}

class ChatRequest(BaseModel):
    message: str

def extract_vin(text):
    # Aggressive VIN cleaning
    clean_text = re.sub(r'\s+', '', text)
    vin_pattern = r'[A-HJ-NPR-Z0-9]{17}'
    match = re.search(vin_pattern, clean_text)
    return match.group(0) if match else "VIN not found"

def calculate_fairness(text):
    score = 100
    issues = []
    t = text.lower()
    
    # HARSH PENALTIES
    if "as-is" in t or "no warranty" in t:
        score -= 30
        issues.append("AS-IS Clause: You have zero protection if the car breaks tomorrow.")
    
    if "non-refundable" in t:
        score -= 20
        issues.append("Non-Refundable Deposit: You lose your money even if you find a major mechanical flaw.")

    if "assumes all risk" in t or "buyer's risk" in t:
        score -= 20
        issues.append("High Liability: Seller is pushing all legal responsibility onto you.")

    # Missing Essentials
    if not re.search(r"price|amount|\$", t):
        score -= 15
        issues.append("Price not clearly defined.")
    
    if "signature" not in t:
        score -= 15
        issues.append("Missing signature lines.")

    return max(0, score), issues

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        doc = fitz.open(file_location)
        text = "".join([page.get_text() for page in doc])
        contract_memory["text"] = text
        
        vin = extract_vin(text)
        score, issues = calculate_fairness(text)
        risk = "Low" if score > 85 else "Medium" if score > 60 else "High"

        return {"vin": vin, "fairness_score": score, "risk_level": risk, "issues": issues}
    finally:
        if os.path.exists(file_location): os.remove(file_location)

@app.get("/vin/{vin_number}")
def vin_lookup(vin_number: str):
    if len(vin_number) < 17: return {"error": "Invalid VIN"}
    res = requests.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin_number}?format=json")
    data = res.json().get("Results", [{}])[0]
    return {
        "Make": data.get("Make", "Unknown"),
        "Model": data.get("Model", "Unknown"),
        "Year": data.get("ModelYear", "Unknown"),
        "Body": data.get("BodyClass", "Unknown")
    }

@app.post("/chat/")
async def chat_assistant(request: ChatRequest):
    prompt = f"""
    CONTRACT CONTEXT: {contract_memory['text'][:3000]}
    USER QUESTION: {request.message}
    
    INSTRUCTIONS: 
    1. Be extremely concise. Use max 3 bullet points.
    2. Use simple language (no legalese).
    3. If it's a bad deal, say it clearly.
    """
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content}
    except:
        return {"response": "I'm a bit overwhelmed. Ask me again in a second!"}
