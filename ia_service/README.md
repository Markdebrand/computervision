# IA Face Verify Service (FastAPI)

Servicio minimal de verificación facial para Odoo.

## Endpoints
- `GET /health` — chequeo básico
- `POST /verify_face` — body JSON: `{ "image_b64": str, "encoding_reference": str }`
  - Respuesta: `{ "match": bool, "distance": float | null, "error": str | null }`

## Requisitos
- Python 3.10+
- Paquetes: ver `requirements.txt`
- Para mejor rendimiento, instalar `dlib` con CUDA para `face_recognition` (opcional y avanzado).

## Ejecutar (desarrollo)
```bash
# crear y activar venv (opcional)
python -m venv .venv
source .venv/bin/activate  # Windows Git Bash
# instalar deps
python -m pip install -r requirements.txt
# iniciar
uvicorn ia_service.main:app --reload --host 0.0.0.0 --port 8000
```

## Notas
- El umbral de coincidencia por defecto es 0.6.
- Asegúrate de exponer `http://<host>:8000/verify_face` y configurar en Odoo el parámetro del sistema `mi_empresa_facial_checkin.ia_api_url`.
