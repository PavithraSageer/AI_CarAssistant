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
    return {"status": "Online", "message": "DealGuard API"}

def extract_vin(text):
    # Regex for 17-char VIN
    clean_text = re.sub(r'\s+', '', text)
    vin_pattern = r'[A-HJ-NPR-Z0-9]{17}'
    match = re.search(vin_pattern, clean_text)
    return match.group(0) if match else "VIN not found"

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
        
        # Scoring logic
        score = 100
        issues = []
        t = text.lower()
        if "as-is" in t or "no warranty" in t:
            score -= 35
            issues.append("AS-IS: No protection if the car breaks.")
        if "non-refundable" in t:
            score -= 25
            issues.append("Non-Refundable: You lose your deposit no matter what.")
        if "assumes all risk" in t:
            score -= 20
            issues.append("High Liability: You take all legal blame.")

        return {"vin": vin, "fairness_score": max(0, score), "issues": issues}
    finally:
        if os.path.exists(file_location): os.remove(file_location)

@app.get("/vin/{vin_number}")
def vin_lookup(vin_number: str):
    # If the frontend passes the string "VIN not found", stop here
    if len(vin_number) < 17:
        return {"error": "Invalid VIN"}
    
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin_number}?format=json"
    res = requests.get(url)
    data = res.json().get("Results", [{}])[0]
    
    return {
        "Make": data.get("Make", "N/A"),
        "Model": data.get("Model", "N/A"),
        "Year": data.get("ModelYear", "N/A"),
        "Body": data.get("BodyClass", "N/A"),
        "Drive": data.get("DriveType", "N/A")
    }

@app.post("/chat/")
async def chat_assistant(request: ChatRequest):
    prompt = f"""
    Context: {contract_memory['text'][:3000]}
    Question: {request.message}
    
    Rules:
    - NO Markdown. Do NOT use stars (**) or hashtags (#). 
    - Use plain text only.
    - Max 3 short bullet points using simple dashes (-).
    - If it's a bad deal, start with: ATTENTION: BAD DEAL.
    """
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content}
    except:
        return {"response": "System busy. Try again!"}
