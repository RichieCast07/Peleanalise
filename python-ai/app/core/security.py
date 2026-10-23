"""Protección del servicio de IA cuando está accesible desde internet."""

import hmac
from urllib.parse import urlparse

from fastapi import Header, HTTPException

from app.core.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Exige X-API-Key si AI_API_KEY está definida (en desarrollo local queda abierto)."""
    expected = settings.AI_API_KEY
    if not expected:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Clave de API inválida o ausente")


def check_image_url(url: str) -> None:
    """
    Evita que el servicio se use para descargar cualquier URL (SSRF): solo http(s) y,
    si ALLOWED_IMAGE_HOSTS está definida, solo esos hosts (o sus subdominios).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL de imagen inválida")

    allowed = [h.strip().lower() for h in settings.ALLOWED_IMAGE_HOSTS.split(",") if h.strip()]
    if allowed:
        host = parsed.hostname.lower()
        if not any(host == a or host.endswith("." + a) for a in allowed):
            raise HTTPException(status_code=400, detail="Host de imagen no permitido")
