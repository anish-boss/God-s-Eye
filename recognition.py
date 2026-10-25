from pathlib import Path
import cv2

DETECTOR_MODEL = Path("models/face_detection_yunet_2023mar.onnx")
RECOGNIZER_MODEL = Path("models/face_recognition_sface_2021dec.onnx")
REFERENCE_IMAGE = Path("reference_faces/target.jpg")

class FaceMatcher:
    """Local one-reference-image matcher using OpenCV YuNet + SFace."""

    def __init__(self, threshold=0.363):
        if not DETECTOR_MODEL.exists() or not RECOGNIZER_MODEL.exists():
            raise FileNotFoundError("Models missing. Run: python download_models.py")
        self.threshold = float(threshold)
        self.detector = cv2.FaceDetectorYN.create(
            str(DETECTOR_MODEL), "", (320, 320), 0.8, 0.3, 5000
        )
        self.recognizer = cv2.FaceRecognizerSF.create(str(RECOGNIZER_MODEL), "")
        self.reference_mtime = None
        self.reference_feature = None
        self.reload_reference(force=True)

    def _faces(self, image):
        self.detector.setInputSize((image.shape[1], image.shape[0]))
        _, faces = self.detector.detect(image)
        return faces

    def reload_reference(self, force=False):
        if not REFERENCE_IMAGE.exists():
            self.reference_feature = None
            raise FileNotFoundError("Upload a reference image in the dashboard first.")
        mtime = REFERENCE_IMAGE.stat().st_mtime
        if not force and self.reference_mtime == mtime:
            return
        image = cv2.imread(str(REFERENCE_IMAGE))
        if image is None:
            raise ValueError("Reference image could not be decoded.")
        faces = self._faces(image)
        if faces is None or len(faces) == 0:
            raise ValueError("No face found. Use a clear, well-lit, front-facing photo.")
        face = max(faces, key=lambda row: float(row[14]))
        aligned = self.recognizer.alignCrop(image, face)
        self.reference_feature = self.recognizer.feature(aligned)
        self.reference_mtime = mtime
        print("[recognition] Reference image loaded locally.")

    def match_frame(self, frame):
        self.reload_reference()
        faces = self._faces(frame)
        results = []
        if faces is None:
            return results
        for face in faces:
            aligned = self.recognizer.alignCrop(frame, face)
            feature = self.recognizer.feature(aligned)
            similarity = float(self.recognizer.match(
                self.reference_feature, feature, cv2.FaceRecognizerSF_FR_COSINE
            ))
            x, y, w, h = [int(v) for v in face[:4]]
            results.append({"box": (x, y, w, h), "similarity": similarity,
                            "match": similarity >= self.threshold})
        return results
