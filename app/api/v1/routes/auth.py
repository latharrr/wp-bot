from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, get_current_user
from app.core.auth import create_access_token, verify_password
from app.core.rate_limit import clear_attempts, is_locked_out, record_failed_attempt
from app.models.api import LoginRequest, LoginResponse, MeResponse
from app.repositories.supabase_admin_repository import SupabaseAdminRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    rate_limit_key = body.username.strip().lower()
    if is_locked_out(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again in a few minutes.",
        )

    admin = SupabaseAdminRepository().get_by_username(body.username)
    if not admin or not verify_password(body.password, admin["password_hash"]):
        record_failed_attempt(rate_limit_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    clear_attempts(rate_limit_key)
    return LoginResponse(access_token=create_access_token(admin["username"]))


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    """The dashboard calls this once after login to decide which nav links/pages to show --
    the backend still independently enforces this per-feature via require_feature(...), this is
    just so the UI doesn't have to guess or attempt-and-fail."""
    return MeResponse(username=user.username, role=user.role, allowed_features=user.allowed_features)
