"""LLM service for extracting SLA fields via OpenRouter API."""

import json
import os
import re
from typing import Dict

import requests
from dotenv import load_dotenv

# Load environment variables from a local .env file.
load_dotenv()

# API key placeholder (replace in .env for local development).
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY")

# OpenRouter endpoint for chat completion requests.
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")

# Model placeholder. You can replace with any OpenRouter-supported model.
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# Required JSON schema keys for strict SLA output.
REQUIRED_SLA_KEYS = [
    "apr",
    "loan_term",
    "monthly_payment",
    "total_payment",
    "due_date",
    "lender_name",
    "borrower_name",
    "vin",
]


def build_sla_prompt(contract_text: str) -> str:
    """Build a strict extraction prompt that forces JSON-only SLA output."""
    # The prompt explicitly asks for strict JSON and no extra narrative text.
    return (
        "You are an expert contract analyzer. Extract the following fields from the contract text. "
        "Return ONLY valid JSON with exactly these keys and string values: "
        '{"apr":"","loan_term":"","monthly_payment":"","total_payment":"","due_date":"","lender_name":"","borrower_name":"","vin":""}. '
        "If a value is missing, return an empty string. Do not include markdown or explanation. "
        "Contract text:\n"
        f"{contract_text}"
    )


def _normalize_sla_json(parsed_data: Dict) -> Dict[str, str]:
    """Normalize parsed JSON so all required keys exist as string values."""
    normalized = {}

    for key in REQUIRED_SLA_KEYS:
        # Keep output stable by forcing missing/null values to empty strings.
        value = parsed_data.get(key, "")
        normalized[key] = "" if value is None else str(value)

    return normalized


def _parse_json_from_llm_content(content: str) -> Dict[str, str]:
    """Parse strict JSON from model content and normalize required SLA keys."""
    # Try direct parsing first (ideal case when model follows instructions).
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return _normalize_sla_json(parsed)
    except json.JSONDecodeError:
        pass

    # Fallback: some models wrap JSON in extra text, so extract the first JSON object.
    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        raise ValueError("LLM response did not contain a valid JSON object.")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as error:
        raise ValueError("LLM returned invalid JSON format.") from error

    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON must be an object.")

    return _normalize_sla_json(parsed)


def extract_sla_with_openrouter(contract_text: str) -> Dict[str, str]:
    """Send OCR text to OpenRouter and return normalized SLA JSON fields."""
    if OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY":
        raise ValueError("OpenRouter API key is not configured.")

    prompt = build_sla_prompt(contract_text)

    # API request body follows OpenRouter chat completion structure.
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You extract contract SLA fields into strict JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Use timeout to avoid hanging requests in production scenarios.
    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()

    # Safely navigate the completion object and validate the expected shape.
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("Unexpected OpenRouter response format.") from error

    return _parse_json_from_llm_content(content)
