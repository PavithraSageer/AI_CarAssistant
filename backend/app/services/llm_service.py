import json
import re
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

EXTRACTION_PROMPT = """
You are an expert automotive finance contract analyst. Analyze the following car lease or loan contract text and extract ALL key SLA fields.

Return ONLY valid JSON with no extra text, no markdown, no backticks. Use null for missing values.

Required JSON structure:
{{
  "contract_type": "lease" or "loan",
  "dealer_offer_name": "string or null",
  "contract_date": "string or null",
  "apr_percent": number or null,
  "money_factor": number or null,
  "term_months": integer or null,
  "monthly_payment": number or null,
  "down_payment": number or null,
  "fees_total": number or null,
  "residual_value": number or null,
  "residual_percent_msrp": number or null,
  "msrp": number or null,
  "cap_cost": number or null,
  "cap_cost_reduction": number or null,
  "mileage_allowance_yr": integer or null,
  "mileage_overage_fee": number or null,
  "early_termination_fee": number or null,
  "disposition_fee": number or null,
  "purchase_option_price": number or null,
  "insurance_requirements": "string or null",
  "maintenance_resp": "string or null",
  "warranty_summary": "string or null",
  "late_fee_policy": "string or null",
  "vehicle_vin": "string or null",
  "vehicle_year": integer or null,
  "vehicle_make": "string or null",
  "vehicle_model": "string or null",
  "vehicle_trim": "string or null",
  "red_flags": ["list of concerning clauses as strings"],
  "negotiation_points": ["list of specific negotiation suggestions as strings"],
  "fairness_score": number between 0-100,
  "fairness_explanation": "string",
  "plain_summary": "A simple 3-4 sentence plain English summary of this contract that anyone can understand. Include the most important numbers and whether this is a good or bad deal."
}}

Contract Text:
{contract_text}
"""

NEGOTIATION_PROMPT = """
You are an expert car lease and loan negotiation coach.
The user is negotiating a car deal and needs your help.

Contract Context:
{contract_context}

User Message: {user_message}

Provide:
1. A helpful response to their question
2. A ready-to-send negotiation message they can use with the dealer (professional, assertive, polite)

Format your response as JSON:
{{
  "response": "your helpful explanation",
  "suggested_dealer_message": "ready-to-send message for the dealer"
}}
"""

COMPARISON_PROMPT = """
You are an automotive finance expert. Compare these two car deals and give a clear recommendation.

Deal 1 (Primary):
{deal1}

Deal 2 (Comparison):
{deal2}

Return JSON:
{{
  "winner": "deal1" or "deal2" or "tie",
  "analysis": "detailed plain-english comparison",
  "savings": number,
  "key_differences": ["list of key differences"]
}}
"""


def extract_sla_from_text(contract_text: str) -> dict:
    """Use Gemini to extract SLA fields from contract text."""
    prompt = EXTRACTION_PROMPT.format(contract_text=contract_text[:12000])
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def get_negotiation_response(contract_context: str, user_message: str) -> dict:
    """Generate negotiation advice and dealer message using Gemini."""
    prompt = NEGOTIATION_PROMPT.format(
        contract_context=contract_context[:4000],
        user_message=user_message,
    )
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"response": raw, "suggested_dealer_message": ""}


def compare_deals(deal1: dict, deal2: dict) -> dict:
    """Compare two contract SLAs and return analysis."""
    prompt = COMPARISON_PROMPT.format(
        deal1=json.dumps(deal1, indent=2),
        deal2=json.dumps(deal2, indent=2),
    )
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"winner": "unknown", "analysis": raw, "savings": 0, "key_differences": []}