import json
import os
from datetime import datetime, timezone
from pathlib import Path

LOCATION_FILE = Path("runtime/location.json")
MAX_AGE_SECONDS = int(os.getenv("LOCATION_MAX_AGE_SECONDS", "60"))

def utc_now():
    return datetime.now(timezone.utc)

def read_latest_location():
    """Return coordinates only when the local device-location fix is valid and fresh."""
    try:
        payload = json.loads(LOCATION_FILE.read_text(encoding="utf-8"))
        lat, lon = float(payload["latitude"]), float(payload["longitude"])
        fix = datetime.fromisoformat(payload["fix_timestamp"].replace("Z", "+00:00"))
        if fix.tzinfo is None:
            fix = fix.replace(tzinfo=timezone.utc)
        age = (utc_now() - fix).total_seconds()
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return {"available": False, "reason": "invalid_coordinates"}
        if age < -10 or age > MAX_AGE_SECONDS:
            return {"available": False, "reason": "stale_location", "age_seconds": round(age, 1)}
        return {
            "available": True, "latitude": lat, "longitude": lon,
            "accuracy_m": payload.get("accuracy_m"),
            "source": payload.get("source", "browser_geolocation"),
            "fix_timestamp": fix.isoformat(), "age_seconds": round(max(age, 0), 1),
        }
    except FileNotFoundError:
        return {"available": False, "reason": "no_location_fix"}
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, OSError):
        return {"available": False, "reason": "invalid_location_feed"}
