from fastapi import APIRouter, HTTPException, status

from app.core.auth import create_access_token, verify_password
from app.models.api import LoginRequest, LoginResponse
from app.repositories.supabase_admin_repository import SupabaseAdminRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    admin = SupabaseAdminRepository().get_by_username(body.username)
    if not admin or not verify_password(body.password, admin["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return LoginResponse(access_token=create_access_token(admin["username"]))
