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

@app.get("/")
def home():
    return {"status": "Online", "message": "DealGuard API is running"}

def extract_vin(text):
    # Cleans spaces and looks for 17 chars
    clean_text = re.sub(r'\s+', '', text)
    vin_pattern = r'[A-HJ-NPR-Z0-9]{17}'
    match = re.search(vin_pattern, clean_text)
    return match.group(0) if match else "VIN not found"

def calculate_fairness(text):
    score = 100
    issues = []
    t = text.lower()
    
    # CRITICAL PENALTIES (To ensure risky deals get ~40%)
    if "as-is" in t or "no warranty" in t:
        score -= 35
        issues.append("AS-IS: No protection if the car breaks.")
    
    if "non-refundable" in t:
        score -= 25
        issues.append("Non-Refundable: You lose your deposit no matter what.")

    if "assumes all risk" in t or "buyer's risk" in t:
        score -= 20
        issues.append("High Liability: You take all legal blame.")

    if "no responsibility" in t or "seller not liable" in t:
        score -= 10
        issues.append("Seller Protection: Seller is legally untouchable.")

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
    if len(vin_number) < 17 or "not found" in vin_number.lower():
        return {"error": "Invalid VIN"}
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
    # Prompt engineering to force SIMPLE, SHORT replies
    prompt = f"""
    Context: {contract_memory['text'][:3000]}
    Question: {request.message}
    
    Rules:
    - Explain like I'm 5 years old.
    - Max 3 short bullet points.
    - If it's a bad deal, start with "⚠️ BAD DEAL."
    """
    try:
        response = client.chat.completions.create(
            model="openrouter/free", # Uses whatever is available
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content}
    except:
        return {"response": "System busy. Try again!"}
