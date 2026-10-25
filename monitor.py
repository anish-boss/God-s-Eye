import os
import threading
import time
from datetime import datetime, timezone

import cv2
from dotenv import load_dotenv
from database import save_event
from location import read_latest_location
from recognition import FaceMatcher

load_dotenv()
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.363"))
COOLDOWN = int(os.getenv("ALERT_COOLDOWN_SECONDS", "30"))
CAMERA_ID = "LAPTOP-CAM-01"

def alert():
    try:
        import winsound
        winsound.Beep(1200, 700)
    except Exception:
        print("\a", end="", flush=True)

def main():
    matcher = FaceMatcher(threshold=THRESHOLD)
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam. Check Windows camera permissions.")

    last_alert_at = 0.0
    print("Monitoring is running. Press Q in the video window to stop.")
    print("Use only with authorized reference images and consenting participants.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("[camera] Frame unavailable; retrying...")
                time.sleep(0.25)
                continue
            try:
                results = matcher.match_frame(frame)
            except (FileNotFoundError, ValueError) as exc:
                cv2.putText(frame, str(exc)[:70], (12, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 2)
                results = []

            now = time.time()
            for result in results:
                x, y, w, h = result["box"]
                matched = result["match"]
                color = (0, 0, 255) if matched else (0, 200, 0)
                label = ("POTENTIAL MATCH" if matched else "Other face") + f" | sim {result['similarity']:.2f}"
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, label, (x, max(20, y-8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                if matched and now - last_alert_at >= COOLDOWN:
                    last_alert_at = now
                    location = read_latest_location()
                    event = {
                        "camera_id": CAMERA_ID,
                        "detected_at": datetime.now(timezone.utc).isoformat(),
                        "location": location if location.get("available") else None,
                        "location_status": location.get("reason", "available"),
                        "similarity": round(result["similarity"], 4),
                        "alert_status": "triggered",
                        "note": "Potential face match; not proof of identity."
                    }
                    threading.Thread(target=alert, daemon=True).start()
                    saved = save_event(event)
                    print(f"[event] Potential match logged ({saved.get('storage', 'unknown storage')}).")
            cv2.imshow("Gods Eye — Local Monitor", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Monitoring stopped.")

if __name__ == "__main__":
    main()
