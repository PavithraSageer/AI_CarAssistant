DealGuard: AI-Driven Contract Auditor 
DealGuard is a minimalist, high-precision digital auditor designed to dismantle the "Jargon Barrier" in automotive financing. By combining high-speed PDF extraction with a weighted risk-scoring algorithm, it transforms 50-page predatory contracts into clear, actionable safety reports.

The Core Mission
Car buyers often face "Legal Fatigue," signing dense contracts containing hidden fees and "As-Is" clauses. DealGuard acts as a Digital Shield, using AI to extract the 5% of text that actually impacts the buyer's wallet.

The Tech Stack
Frontend: React.js (Clean, Sidebar-free UI for cognitive focus)
Backend: FastAPI (High-concurrency Python framework)
Database: Supabase (PostgreSQL with Row-Level Security)
AI Engine: Arcee Trinity-Mini (Tuned to 0.3 Temperature for factual precision)
Parsing: PyMuPDF (fitz) & Regex Pattern Matching

Key Features
1. The X-Ray Pipeline
    Uses PyMuPDF to bypass slow OCR, extracting the raw text layer in milliseconds. Custom Regex logic identifies the 17-character VIN and financial figures before the AI even starts, saving tokens and ensuring 100% accuracy on vehicle data.
2. Weighted Fairness Algorithm
   Instead of subjective summaries, DealGuard calculates a Fairness Score (0–100).
   -35 Points: "As-Is" / No Warranty clauses.
   -20 Points: Uncapped Administrative Fees.
   -15 Points: Ambiguous Arbitration Waivers.
3. Jargon-to-English Chatbot
    A specialized implementation of the Trinity-Mini LLM that acts as a contract consultant. Tuned for low-temperature (0.3) determinism, it translates complex legalese into 5th-grade English without "hallucinating" advice.

Future Roadmap
Automated Negotiation: Generating structured dispute letters based on detected red flags.
Domain Expansion: Porting the auditing logic to Home Rental Agreements and Insurance Policies.
Historical Benchmarking: Tracking dealership patterns to identify recurring predatory behavior.

Installation & Setup
Clone the repository:
  Bash
   git clone https://github.com/your-username/dealguard.git
Setup Backend:
  Bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
Setup Frontend:
  Bash
   cd frontend
   npm install
   npm start

Author
Pavithra S |AI Domain Intern 
