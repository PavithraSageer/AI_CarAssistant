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

# In-memory storage for the AI context
contract_memory = {"text": ""}

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "Online", "service": "DealGuard"}

def get_vehicle_details(vin):
    if not vin or len(vin) < 17 or "not found" in vin.lower():
        return None
    try:
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
        res = requests.get(url, timeout=5)
        data = res.json().get("Results", [{}])[0]
        # Consolidating specs into a clean object
        return {
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
        
        # Aggressive VIN extraction (strips spaces first)
        clean_text = re.sub(r'\s+', '', text)
        vin_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', clean_text)
        vin = vin_match.group(0) if vin_match else "Not Found"
        
        # Fetch specs immediately so the frontend has them in one go
        specs = get_vehicle_details(vin)
        
        # Harsher scoring for risky deals
        score = 100
        issues = []
        t = text.lower()
        if "as-is" in t or "no warranty" in t:
            score -= 35
            issues.append("AS-IS: No protection if the car breaks.")
        if "non-refundable" in t:
            score -= 25
            issues.append("Non-Refundable Deposit: High risk of losing money.")
        if "assumes all risk" in t:
            score -= 20
            issues.append("High Liability: Seller is not responsible for defects.")

        return {
            "vin": vin,
            "fairness_score": max(0, score),
            "risk_level": "High" if score < 60 else "Medium" if score < 85 else "Low",
            "issues": issues,
            "specs": specs # Included in the primary response
        }
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)

@app.post("/chat/")
async def chat_assistant(request: ChatRequest):
    # Strict prompt to stop Markdown (the ** stars)
    prompt = f"""
    Context: {contract_memory['text'][:3000]}
    Question: {request.message}
    
    Rules:
    - Use PLAIN TEXT ONLY. 
    - DO NOT use any stars (**) or hashtags (#).
    - Max 3 short bullet points using simple dashes (-).
    - Be conversational and very simple.
    """
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content}
    except:
        return {"response": "I'm a bit busy. Please ask again!"}
