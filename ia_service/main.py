from fastapi import FastAPI
from pydantic import BaseModel
import base64
import io
from typing import Optional

import numpy as np
from PIL import Image

try:
    import face_recognition  # dlib-based
except Exception:
    face_recognition = None

app = FastAPI(title="IA Face Verify Service", version="0.1.0")


class FaceVerificationRequest(BaseModel):
    image_b64: str
    encoding_reference: str


class FaceVerificationResponse(BaseModel):
    match: bool
    distance: Optional[float] = None
    error: Optional[str] = None


class FaceVerifyWithImageRequest(BaseModel):
    image_b64: str
    reference_image_b64: str


def load_image_from_base64(b64_string: str) -> np.ndarray:
    """Convierte base64 (con o sin prefijo data:) a imagen RGB numpy."""
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[-1]
    img_data = base64.b64decode(b64_string)
    img_file = io.BytesIO(img_data)
    image = Image.open(img_file).convert("RGB")
    return np.array(image)


def string_to_encoding(encoding_str: str) -> np.ndarray:
    """Convierte string estilo "[0.1, 0.2, ...]" a np.array(float)."""
    s = encoding_str.strip().strip("[]")
    if not s:
        return np.array([], dtype=float)
    return np.array([float(x) for x in s.split(',')], dtype=float)


@app.get("/health")
async def health():
    return {"status": "ok", "face_recognition": bool(face_recognition)}


@app.post("/verify_face", response_model=FaceVerificationResponse)
async def verify_face(request: FaceVerificationRequest):
    try:
        if face_recognition is None:
            return FaceVerificationResponse(match=False, error="face_recognition no disponible en el servidor")

        known_encoding = string_to_encoding(request.encoding_reference)
        if known_encoding.size == 0:
            return FaceVerificationResponse(match=False, error="Encoding de referencia vacío o inválido")

        unknown_image = load_image_from_base64(request.image_b64)
        unknown_encodings = face_recognition.face_encodings(unknown_image)
        if not unknown_encodings:
            return FaceVerificationResponse(match=False, error="No se detectó un rostro en la imagen")

        distance = float(face_recognition.face_distance([known_encoding], unknown_encodings[0])[0])
        is_match = distance <= 0.6
        return FaceVerificationResponse(match=is_match, distance=distance)

    except Exception as e:
        return FaceVerificationResponse(match=False, error=str(e))


@app.post("/verify_face_image", response_model=FaceVerificationResponse)
async def verify_face_image(request: FaceVerifyWithImageRequest):
    """Compara una imagen desconocida contra una imagen de referencia (ambas en base64)."""
    try:
        if face_recognition is None:
            return FaceVerificationResponse(match=False, error="face_recognition no disponible en el servidor")

        # cargar imágenes
        unknown_image = load_image_from_base64(request.image_b64)
        ref_image = load_image_from_base64(request.reference_image_b64)

        # obtener encodings
        ref_encodings = face_recognition.face_encodings(ref_image)
        if not ref_encodings:
            return FaceVerificationResponse(match=False, error="No se detectó un rostro en la imagen de referencia")

        unknown_encodings = face_recognition.face_encodings(unknown_image)
        if not unknown_encodings:
            return FaceVerificationResponse(match=False, error="No se detectó un rostro en la imagen enviada")

        distance = float(face_recognition.face_distance([ref_encodings[0]], unknown_encodings[0])[0])
        is_match = distance <= 0.6
        return FaceVerificationResponse(match=is_match, distance=distance)
    except Exception as e:
        return FaceVerificationResponse(match=False, error=str(e))
