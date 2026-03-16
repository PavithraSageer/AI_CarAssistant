from fastapi import FastAPI, UploadFile, File
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
    return {"status": "Online"}

def get_vehicle_details(vin):
    if not vin or len(vin) < 17 or "not found" in vin.lower():
        return None
    try:
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
        res = requests.get(url, timeout=5)
        data = res.json().get("Results", [{}])[0]
        # Return both casing formats to be 100% safe for the frontend
        return {
            "make": data.get("Make"),
            "model": data.get("Model"),
            "year": data.get("ModelYear"),
            "body": data.get("BodyClass"),
            "Make": data.get("Make"),
            "Model": data.get("Model"),
            "Year": data.get("ModelYear"),
            "Body": data.get("BodyClass")
        }
    except:
        return None

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        doc = fitz.open(file_location)
        text = "".join([page.get_text() for page in doc])
        contract_memory["text"] = text
        
        # Aggressive VIN cleaning
        clean_text = re.sub(r'\s+', '', text)
        vin_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', clean_text)
        vin = vin_match.group(0) if vin_match else "Not Found"
        
        specs = get_vehicle_details(vin)
        
        score = 100
        issues = []
        t = text.lower()
        if "as-is" in t or "no warranty" in t: score -= 35; issues.append("AS-IS: No protection.")
        if "non-refundable" in t: score -= 25; issues.append("Non-Refundable Deposit.")
        if "assumes all risk" in t: score -= 20; issues.append("High Liability.")

        return {
            "vin": vin,
            "fairness_score": max(0, score),
            "issues": issues,
            "specs": specs
        }
    finally:
        if os.path.exists(file_location): os.remove(file_location)

@app.post("/chat/")
async def chat_assistant(request: ChatRequest):
    prompt = f"Contract: {contract_memory['text'][:3000]}\nQuestion: {request.message}\nRules: Plain text, no stars, no markdown, max 3 points."
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content}
    except:
        return {"response": "System busy."}
