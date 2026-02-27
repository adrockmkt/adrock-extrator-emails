import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==============================
# CONFIG
# ==============================

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)
API_USAGE_FILE = STATE_DIR / "api_usage.json"

TEXT_SEARCH_COST = 0.017
DETAILS_COST = 0.017

DAILY_BUDGET_USD = 5.0
EXECUTION_BUDGET_USD = 2.0

# ==============================
# STATE MANAGEMENT
# ==============================

_RUN_SPENT_USD = 0.0


def _today_str_local():
    return datetime.now().strftime("%Y-%m-%d")


def _default_usage(today):
    return {
        "date": today,
        "daily_spent_usd": 0.0,
        "calls_text_search": 0,
        "calls_details": 0,
    }


def _normalize_usage(data, today):
    if not isinstance(data, dict):
        return _default_usage(today)

    if data.get("date") != today:
        return _default_usage(today)

    normalized = _default_usage(today)
    normalized.update(data)

    try:
        normalized["daily_spent_usd"] = float(normalized.get("daily_spent_usd", 0.0) or 0.0)
    except Exception:
        normalized["daily_spent_usd"] = 0.0

    for k in ("calls_text_search", "calls_details"):
        try:
            normalized[k] = int(normalized.get(k, 0) or 0)
        except Exception:
            normalized[k] = 0

    normalized["date"] = today
    return normalized


def load_api_usage():
    today = _today_str_local()

    if not API_USAGE_FILE.exists():
        return _default_usage(today)

    try:
        with open(API_USAGE_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return _default_usage(today)

    return _normalize_usage(data, today)


def save_api_usage(data):
    today = _today_str_local()
    data = _normalize_usage(data, today)

    with open(API_USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def can_spend(amount):
    global _RUN_SPENT_USD
    usage = load_api_usage()

    if _RUN_SPENT_USD + amount > EXECUTION_BUDGET_USD:
        return False

    if usage["daily_spent_usd"] + amount > DAILY_BUDGET_USD:
        return False

    return True


def register_spend(amount, call_type):
    global _RUN_SPENT_USD
    usage = load_api_usage()

    usage["daily_spent_usd"] = float(usage.get("daily_spent_usd", 0.0) or 0.0) + amount
    _RUN_SPENT_USD += amount

    if call_type == "text_search":
        usage["calls_text_search"] = int(usage.get("calls_text_search", 0) or 0) + 1
    elif call_type == "details":
        usage["calls_details"] = int(usage.get("calls_details", 0) or 0) + 1

    save_api_usage(usage)

# ==============================
# GOOGLE PLACES CLIENT
# ==============================


def search_place(company_name):
    if not API_KEY:
        raise Exception("GOOGLE_MAPS_API_KEY não configurada no .env")

    if not can_spend(TEXT_SEARCH_COST):
        raise Exception("Budget exceeded (Text Search).")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {
        "query": company_name,
        "key": API_KEY,
    }

    response = requests.get(url, params=params, timeout=30)
    data = response.json() if response is not None else {}

    register_spend(TEXT_SEARCH_COST, "text_search")

    results = data.get("results")
    if not results:
        return None

    return results[0].get("place_id")


def get_place_details(place_id):
    if not API_KEY:
        raise Exception("GOOGLE_MAPS_API_KEY não configurada no .env")

    if not can_spend(DETAILS_COST):
        raise Exception("Budget exceeded (Details).")

    url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "name,website",
        "key": API_KEY,
    }

    response = requests.get(url, params=params, timeout=30)
    data = response.json() if response is not None else {}

    register_spend(DETAILS_COST, "details")

    result = data.get("result")
    if not result:
        return None

    return result.get("website")

# ==============================
# PUBLIC FUNCTION
# ==============================


def get_company_website(company_name):
    try:
        place_id = search_place(company_name)
        if not place_id:
            return None

        website = get_place_details(place_id)
        if not website:
            return None

        return website

    except Exception as e:
        print(f"[PLACES ERROR] {e}")
        return None