"""
storage.py — Persistance JSON pour AUI Email Support System.
Sauvegarde les resultats dans data/reports/report.json.
"""

from __future__ import annotations
import json
import threading
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

REPORT_PATH = Path(__file__).parent.parent / "data" / "reports" / "report.json"


class Storage:

    def __init__(self, path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.path = path or REPORT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._data = self._load()

    def _load(self) -> dict:
        with self._lock:
            if self.path.exists():
                try:
                    with open(self.path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
            return {"emails": [], "meta": {"created_at": self._now(), "last_updated": self._now(), "total": 0}}

    def _save(self) -> None:
        with self._lock:
            self._data["meta"]["last_updated"] = self._now()
            self._data["meta"]["total"]        = len(self._data["emails"])
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def save_email(self, record: dict) -> None:
        with self._lock:
            for i, e in enumerate(self._data["emails"]):
                if e.get("id") == record.get("id"):
                    self._data["emails"][i] = record
                    self._save()
                    return
            record.setdefault("saved_at", self._now())
            self._data["emails"].append(record)
            self._save()

    def get_all(self) -> list:
        with self._lock:
            return list(self._data["emails"])

    def get_by_id(self, email_id: str) -> Optional[dict]:
        with self._lock:
            for e in self._data["emails"]:
                if e.get("id") == email_id:
                    return dict(e)
            return None

    def get_processed_ids(self) -> set:
        with self._lock:
            return {e["id"] for e in self._data["emails"] if "id" in e}

    def get_stats(self) -> dict:
        with self._lock:
            emails = list(self._data["emails"])
        if not emails:
            return {"total": 0, "by_category": {}, "by_language": {}, "by_urgency": {}, "sent": 0, "avg_confidence": 0}

        by_cat: dict  = {}
        by_lang: dict = {}
        by_urg: dict  = {}
        sent          = 0
        conf_sum      = 0.0
        conf_n        = 0

        for e in emails:
            cat  = e.get("category", "unknown")
            lang = e.get("detection", {}).get("language", "unknown")
            urg  = e.get("detection", {}).get("urgency", "unknown")
            by_cat[cat]   = by_cat.get(cat, 0)   + 1
            by_lang[lang] = by_lang.get(lang, 0) + 1
            by_urg[urg]   = by_urg.get(urg, 0)   + 1
            if e.get("sent"):
                sent += 1
            conf = e.get("confidence")
            if conf is not None:
                conf_sum += conf
                conf_n   += 1

        return {
            "total":          len(emails),
            "sent":           sent,
            "avg_confidence": round(conf_sum / conf_n, 3) if conf_n else 0,
            "by_category":    by_cat,
            "by_language":    by_lang,
            "by_urgency":     by_urg,
        }

    def reset(self) -> None:
        with self._lock:
            self._data = {"emails": [], "meta": {"created_at": self._now(), "last_updated": self._now(), "total": 0}}
            self._save()
