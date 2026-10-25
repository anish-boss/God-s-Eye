from pathlib import Path
from urllib.request import urlretrieve

MODELS = {
    "face_detection_yunet_2023mar.onnx": (
        "https://raw.githubusercontent.com/opencv/opencv_zoo/main/"
        "models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    ),
    "face_recognition_sface_2021dec.onnx": (
        "https://raw.githubusercontent.com/opencv/opencv_zoo/main/"
        "models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
    ),
}

def main():
    folder = Path("models")
    folder.mkdir(parents=True, exist_ok=True)
    for name, url in MODELS.items():
        path = folder / name
        if path.exists() and path.stat().st_size > 100_000:
            print(f"Already downloaded: {path}")
            continue
        print(f"Downloading {name}...")
        try:
            urlretrieve(url, path)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        if path.stat().st_size < 100_000:
            path.unlink(missing_ok=True)
            raise RuntimeError(f"Download incomplete: {name}")
        print(f"Saved {path}")
    print("Models ready.")

if __name__ == "__main__":
    main()
