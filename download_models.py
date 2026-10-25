from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

# Official OpenCV Zoo model files. Hashes detect HTML/error pages and corrupted downloads.
MODELS = {
    "face_detection_yunet_2023mar.onnx": {
        "url": "https://huggingface.co/opencv/opencv_zoo/resolve/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    },
    "face_recognition_sface_2021dec.onnx": {
        "url": "https://huggingface.co/opencv/opencv_zoo/resolve/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
    },
}

def download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "The-Gods-Eye-educational-project"})
    with urlopen(request, timeout=90) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)

def main() -> None:
    folder = Path(__file__).resolve().parent / "models"
    folder.mkdir(parents=True, exist_ok=True)
    for name, info in MODELS.items():
        path = folder / name
        expected = info["sha256"]
        if path.exists() and sha256(path.read_bytes()).hexdigest() == expected:
            print(f"Already verified: {path}")
            continue
        path.unlink(missing_ok=True)
        print(f"Downloading {name} from official OpenCV Zoo…")
        try:
            download(info["url"], path)
            actual = sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(
                    f"Checksum mismatch for {name}. Expected {expected}, got {actual}. "
                    "Delete the partial file and retry."
                )
        except Exception:
            path.unlink(missing_ok=True)
            raise
        print(f"Verified and saved: {path}")
    print("All model files downloaded and checksum-verified.")

if __name__ == "__main__":
    main()
