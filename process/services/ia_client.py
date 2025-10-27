import os
import base64
from typing import Dict, Any, Optional

import cv2
import requests


def _img_bgr_to_b64(img_bgr) -> str:
    """Encode cv2 BGR image to base64 (JPEG). Returns base64 string without data URL prefix."""
    if img_bgr is None or img_bgr.size == 0:
        return ""
    ok, buf = cv2.imencode('.jpg', img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode('utf-8')


def verify_with_ref_image(
    image_bgr,
    ref_image_bgr,
    base_url: Optional[str] = None,
    timeout: float = 2.5,
) -> Dict[str, Any]:
    """
    Calls IA service /verify_face_image sending both images as base64.
    Returns dict like {"match": bool, "distance": float|None, "error": str|None}.
    """
    # Defaults: use IA_SERVICE_URL or fallback to localhost
    base_url = base_url or os.getenv('IA_SERVICE_URL') or 'http://localhost:8000'
    url = base_url.rstrip('/') + '/verify_face_image'

    img_b64 = _img_bgr_to_b64(image_bgr)
    ref_b64 = _img_bgr_to_b64(ref_image_bgr)
    if not img_b64 or not ref_b64:
        return {"match": False, "distance": None, "error": "Imagen vacía o inválida"}

    payload = {
        "image_b64": img_b64,
        "reference_image_b64": ref_b64,
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # normalize expected fields
        return {
            "match": bool(data.get("match", False)),
            "distance": data.get("distance"),
            "error": data.get("error"),
        }
    except Exception as e:
        return {"match": False, "distance": None, "error": str(e)}


def health_check(base_url: Optional[str] = None, timeout: float = 1.5) -> bool:
    """Comprueba si el microservicio IA está disponible (GET /health)."""
    base_url = base_url or os.getenv('IA_SERVICE_URL') or 'http://localhost:8000'
    url = base_url.rstrip('/') + '/health'
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return bool(data)
    except Exception:
        return False
