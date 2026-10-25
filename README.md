# The Gods Eye

**A local-first webcam face-matching and alert prototype** built with Python, OpenCV, FastAPI, and an optional MongoDB Atlas event store.

> This is an educational prototype, not an identity-verification system. Face similarity can produce false positives and must never be treated as proof of identity or wrongdoing. Use only reference images you are authorized to process and test with consenting participants.

## Features

- Local webcam monitoring using OpenCV YuNet and SFace models.
- A local web dashboard for uploading one reference image.
- Visual labels for other faces and potential matches, plus a configurable alert cooldown.
- Timestamped event metadata, with optional fresh device geolocation.
- Optional MongoDB Atlas storage for event metadata; local JSONL fallback when Atlas is not configured.
- Reference images and webcam frames stay on the local computer and are not uploaded to MongoDB.

## Project structure

```text
God-s-Eye/
├── main.py                 # FastAPI dashboard and API
├── monitor.py              # Local webcam monitor
├── recognition.py          # YuNet + SFace matching
├── database.py             # Event metadata storage
├── location.py             # Freshness-checked local location
├── download_models.py      # Downloads OpenCV model files
├── requirements.txt
├── .env.example
├── .gitignore
├── static/
│   └── index.html          # Dashboard UI
├── reference_faces/
│   └── README.md           # Keep private reference photos local
└── runtime/
    └── .gitkeep            # Runtime files are generated locally
```

## Requirements

- Windows 10/11 (PowerShell instructions below)
- Python 3.11 recommended
- Webcam and internet access for installing dependencies, downloading models, and map tiles
- MongoDB Atlas is optional; local JSONL storage is used when no URI is configured

## Setup on Windows

Open PowerShell in the project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python download_models.py
```

If PowerShell blocks virtual-environment activation, use a terminal where activation is permitted or run the environment's Python directly: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

The model downloader should create `models/` and download the two ONNX files. Model files are intentionally not committed to Git.

## Run the dashboard and monitor

**Terminal 1 — dashboard:**

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Upload a clear, well-lit reference image containing one face. Optionally enable device location and grant browser permission.

**Terminal 2 — webcam monitor:**

```powershell
.\.venv\Scripts\Activate.ps1
python monitor.py
```

Press `Q` while the webcam window is selected to stop monitoring. The dashboard does not start the monitor automatically; start it in the second terminal. If you replace the reference image while monitoring, restart `monitor.py`.

## Configuration

Edit your local `.env` file. Do not commit it.

- `MONGODB_URI`: leave blank to use local JSONL storage, or set your Atlas connection URI.
- `MONGODB_DATABASE`: database name (default `gods_eye`).
- `MONGODB_COLLECTION`: event collection (default `detection_events`).
- `CAMERA_INDEX`: webcam index (default `0`).
- `MATCH_THRESHOLD`: similarity threshold; calibrate carefully with a consented test set.
- `ALERT_COOLDOWN_SECONDS`: minimum seconds between alerts.
- `LOCATION_MAX_AGE_SECONDS`: maximum age of a location fix accepted for an event.

## Privacy and security

- Keep the service bound to `127.0.0.1`. The starter dashboard does not provide authentication and must not be exposed to a LAN or public internet.
- Never commit `.env`, passwords, private reference photos, model binaries, or runtime logs.
- Browser geolocation represents the device's reported location, not the location of the person in the camera.
- If location is unavailable or stale, events should not use fabricated coordinates.
- Events store metadata only; no webcam frames or reference images are sent to Atlas.
- Face matching may be wrong due to lighting, pose, camera quality, or model limitations. Use human review and do not make consequential decisions based solely on a match.

## Troubleshooting

- **Models missing:** run `python download_models.py` and verify both ONNX files exist in `models/`.
- **Webcam unavailable:** close other camera applications, check Windows camera permissions, and try `CAMERA_INDEX=1`.
- **No face in reference image:** use a clear, front-facing image with one face.
- **Location unavailable:** check browser and Windows location permissions; the app can continue without coordinates.
- **Atlas connection fails:** check the URI, database user, network access list, and URL-encode special characters in the password. Leave `MONGODB_URI` blank for local development.

## Status

Starter prototype for local development. The end-to-end flow should be tested on the target computer before demonstration or use.
