from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.auth import decode_access_token
from app.core.config import get_settings


async def get_current_admin(authorization: Optional[str] = Header(default=None)) -> str:
    """Requires a valid dashboard JWT: 'Authorization: Bearer <token>'."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    subject = decode_access_token(token)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return subject


async def require_internal_token(x_internal_token: Optional[str] = Header(default=None)) -> None:
    """Guards bridge -> Python webhooks. Never accepts the dashboard JWT or the public API key."""
    settings = get_settings()
    if not x_internal_token or x_internal_token != settings.whatsapp_internal_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal token")


async def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Reserved for any future machine-to-machine public endpoints; the dashboard itself uses JWT."""
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
