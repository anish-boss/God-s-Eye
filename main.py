import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from database import list_events

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
REFERENCE_DIR = BASE / "reference_faces"
RUNTIME_DIR = BASE / "runtime"
LOCATION_FILE = RUNTIME_DIR / "location.json"
TARGET_FILE = REFERENCE_DIR / "target.jpg"

app = FastAPI(title="Gods Eye Local Dashboard", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

class LocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)
    fix_timestamp: str
    source: str = "browser_geolocation"

@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")

@app.get("/api/status")
def status():
    return {
        "reference_uploaded": TARGET_FILE.exists(),
        "location_feed_present": LOCATION_FILE.exists(),
        "privacy": "Face matching runs locally; event metadata may be sent to MongoDB Atlas."
    }

@app.post("/api/reference")
async def upload_reference(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Image could not be decoded.")
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    if TARGET_FILE.exists():
        TARGET_FILE.unlink()
    if not cv2.imwrite(str(TARGET_FILE), image):
        raise HTTPException(status_code=500, detail="Could not save reference image.")
    return {"ok": True, "message": "Reference image saved locally. Start or restart the monitor."}

@app.post("/api/location")
def update_location(location: LocationUpdate):
    try:
        fix = datetime.fromisoformat(location.fix_timestamp.replace("Z", "+00:00"))
        if fix.tzinfo is None:
            fix = fix.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid fix_timestamp.")
    payload = location.model_dump()
    payload["fix_timestamp"] = fix.astimezone(timezone.utc).isoformat()
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOCATION_FILE.write_text(json.dumps(payload), encoding="utf-8")
    return {"ok": True, "message": "Location stored locally."}

@app.get("/api/events")
def events(limit: int = 50):
    return list_events(limit)
