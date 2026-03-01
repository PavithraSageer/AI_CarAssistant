"""VIN service for vehicle detail lookup using NHTSA VPIC API."""

import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

# Load environment variables from a local .env file.
load_dotenv()

# NHTSA API base URL placeholder (kept explicit per project requirement).
NHTSA_API_URL = os.getenv(
    "NHTSA_API_URL",
    "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/",
)


def get_vehicle_details(vin: str) -> Dict[str, Any]:
    """Fetch and normalize vehicle details for a VIN from the NHTSA API."""
    clean_vin = (vin or "").strip().upper()

    # VINs are expected to be exactly 17 characters for standard decoding.
    if len(clean_vin) != 17:
        raise ValueError("VIN must be exactly 17 characters.")

    # Build URL exactly as required by NHTSA documentation.
    request_url = f"{NHTSA_API_URL}{clean_vin}?format=json"

    # Send the API request with timeout to avoid indefinite waits.
    response = requests.get(request_url, timeout=30)
    response.raise_for_status()

    payload = response.json()
    results = payload.get("Results", [])
    if not results:
        raise ValueError("No vehicle details found for this VIN.")

    item = results[0]

    # Extract only required fields to keep response clean and predictable.
    return {
        "vin": clean_vin,
        "make": item.get("Make", "") or "",
        "model": item.get("Model", "") or "",
        "model_year": item.get("ModelYear", "") or "",
        "recalls": item.get("Recalls") if item.get("Recalls") else None,
    }
