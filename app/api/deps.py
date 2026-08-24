from dataclasses import dataclass, field

from fastapi import Depends, Header, HTTPException, status

from app.core.auth import decode_access_token
from app.core.config import get_settings
from app.repositories.supabase_admin_repository import SupabaseAdminRepository


@dataclass
class CurrentUser:
    username: str
    role: str
    allowed_features: list[str] = field(default_factory=list)


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """Requires a valid dashboard JWT: 'Authorization: Bearer <token>'. Looks the user back up by
    username (rather than trusting role/features baked into the token) so a super_admin revoking
    or changing someone's feature access takes effect on their very next request, not just after
    their token expires."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    admin = SupabaseAdminRepository().get_by_username(username)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return CurrentUser(
        username=username, role=admin.get("role", "user"), allowed_features=admin.get("allowed_features") or []
    )


async def get_current_admin(user: CurrentUser = Depends(get_current_user)) -> str:
    """Back-compat shim for routes that only need 'is this an authenticated user' plus their
    username (e.g. for audit-log actor fields) -- not a per-feature access check."""
    return user.username


async def require_super_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    return user


def require_feature(feature: str):
    """Router-level dependency: `APIRouter(..., dependencies=[Depends(require_feature('groups'))])`
    gates every route under that router. A super_admin always passes regardless of
    allowed_features."""

    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role != "super_admin" and feature not in user.allowed_features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have access to the '{feature}' feature"
            )
        return user

    return _check


async def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    """Guards bridge -> Python webhooks. Never accepts the dashboard JWT or the public API key."""
    settings = get_settings()
    if not x_internal_token or x_internal_token != settings.whatsapp_internal_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal token")


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Reserved for any future machine-to-machine public endpoints; the dashboard itself uses JWT."""
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
