import re
import requests

def extract_vin(contract_text: str):
    vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    matches = re.findall(vin_pattern, contract_text)
    return matches[0] if matches else None


def fetch_vehicle_data(vin: str):
    api_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        results = response.json().get("Results", [])

        vehicle_data = {}

        for item in results:
            if item["Variable"] in ["Make", "Model", "Model Year"]:
                vehicle_data[item["Variable"]] = item["Value"]

        return vehicle_data

    except Exception as e:
        return {"error": f"VIN lookup failed: {str(e)}"}
