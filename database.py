import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
_client = None
_collection = None
LOCAL_EVENTS = Path("runtime/events.jsonl")

def _mongo_collection():
    global _client, _collection
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        return None
    if _collection is None:
        from pymongo import MongoClient
        _client = MongoClient(uri, serverSelectionTimeoutMS=2500)
        _client.admin.command("ping")
        _collection = _client[os.getenv("MONGODB_DATABASE", "gods_eye")][
            os.getenv("MONGODB_COLLECTION", "detection_events")
        ]
        _collection.create_index("detected_at")
        _collection.create_index("camera_id")
    return _collection

def save_event(event):
    """Store event metadata only; never send frames or reference images to Atlas."""
    record = dict(event)
    record.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    try:
        collection = _mongo_collection()
        if collection is not None:
            result = collection.insert_one(record)
            record["_id"] = str(result.inserted_id)
            record["storage"] = "mongodb_atlas"
            return record
    except Exception as exc:
        print(f"[database] Atlas unavailable; saving locally: {exc}")
    LOCAL_EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with LOCAL_EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    record["storage"] = "local_fallback"
    return record

def list_events(limit=50):
    limit = max(1, min(int(limit), 200))
    try:
        collection = _mongo_collection()
        if collection is not None:
            docs = list(collection.find(
                {}, {"_id": 1, "camera_id": 1, "detected_at": 1,
                     "location": 1, "similarity": 1, "alert_status": 1}
            ).sort("detected_at", -1).limit(limit))
            for doc in docs:
                doc["_id"] = str(doc.get("_id", ""))
                doc["storage"] = "mongodb_atlas"
            return docs
    except Exception as exc:
        print(f"[database] Could not read Atlas; checking local events: {exc}")
    if not LOCAL_EVENTS.exists():
        return []
    rows = []
    for line in LOCAL_EVENTS.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    rows.reverse()
    return rows
