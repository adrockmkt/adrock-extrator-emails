import json
import os
from datetime import datetime
from typing import Dict, Any


class StateManager:
    def __init__(self, state_dir: str = "state"):
        self.state_dir = state_dir
        os.makedirs(self.state_dir, exist_ok=True)

        self.domains_file = os.path.join(self.state_dir, "processed_domains.json")
        self.api_usage_file = os.path.join(self.state_dir, "api_usage.json")

        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(self.domains_file):
            with open(self.domains_file, "w") as f:
                json.dump({}, f, indent=2)

        if not os.path.exists(self.api_usage_file):
            with open(self.api_usage_file, "w") as f:
                json.dump(
                    {
                        "date": datetime.utcnow().strftime("%Y-%m-%d"),
                        "calls_today": 0
                    },
                    f,
                    indent=2
                )

    # =============================
    # DOMAIN STATE
    # =============================

    def load_domains(self) -> Dict[str, Any]:
        with open(self.domains_file, "r") as f:
            return json.load(f)

    def save_domains(self, data: Dict[str, Any]):
        with open(self.domains_file, "w") as f:
            json.dump(data, f, indent=2)

    def is_processed(self, domain: str) -> bool:
        data = self.load_domains()
        return domain in data and data[domain].get("crawled", False)

    def mark_enriched(self, domain: str, segment: str):
        data = self.load_domains()
        if domain not in data:
            data[domain] = {}
        data[domain]["enriched"] = True
        data[domain]["segment"] = segment
        data[domain]["last_updated"] = datetime.utcnow().isoformat()
        self.save_domains(data)

    def mark_crawled(self, domain: str, emails_found: int):
        data = self.load_domains()
        if domain not in data:
            data[domain] = {}
        data[domain]["crawled"] = True
        data[domain]["emails_found"] = emails_found
        data[domain]["last_updated"] = datetime.utcnow().isoformat()
        self.save_domains(data)

    def get_pending_domains(self, domains: list) -> list:
        data = self.load_domains()
        return [d for d in domains if d not in data or not data[d].get("crawled", False)]

    # =============================
    # API USAGE CONTROL
    # =============================

    def load_api_usage(self) -> Dict[str, Any]:
        with open(self.api_usage_file, "r") as f:
            return json.load(f)

    def increment_api_calls(self, amount: int = 1):
        data = self.load_api_usage()
        today = datetime.utcnow().strftime("%Y-%m-%d")

        if data.get("date") != today:
            data["date"] = today
            data["calls_today"] = 0

        data["calls_today"] += amount

        with open(self.api_usage_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_calls_today(self) -> int:
        data = self.load_api_usage()
        today = datetime.utcnow().strftime("%Y-%m-%d")

        if data.get("date") != today:
            return 0

        return data.get("calls_today", 0)

    def can_call_api(self, daily_limit: int) -> bool:
        return self.get_calls_today() < daily_limit
