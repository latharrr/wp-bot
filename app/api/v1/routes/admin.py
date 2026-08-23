from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, require_super_admin
from app.core.auth import hash_password
from app.core.features import AVAILABLE_FEATURES
from app.models.api import CreateUserRequest, UpdateUserFeaturesRequest
from app.repositories.supabase_admin_repository import SupabaseAdminRepository

router = APIRouter(prefix="/admin/users", tags=["admin"])


def _validate_features(features: list[str]) -> None:
    invalid = sorted(set(features) - set(AVAILABLE_FEATURES))
    if invalid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown feature(s): {invalid}")


@router.get("/features")
def list_available_features(_: CurrentUser = Depends(require_super_admin)) -> list[str]:
    return AVAILABLE_FEATURES


@router.get("")
def list_users(_: CurrentUser = Depends(require_super_admin)) -> list[dict]:
    return SupabaseAdminRepository().list_users()


@router.post("")
def create_user(body: CreateUserRequest, _: CurrentUser = Depends(require_super_admin)) -> dict:
    repo = SupabaseAdminRepository()
    if repo.get_by_username(body.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    _validate_features(body.allowed_features)
    repo.create(body.username, hash_password(body.password), role="user", allowed_features=body.allowed_features)
    return {"username": body.username, "role": "user", "allowed_features": body.allowed_features}


@router.patch("/{username}/features")
def update_user_features(
    username: str, body: UpdateUserFeaturesRequest, _: CurrentUser = Depends(require_super_admin)
) -> dict:
    repo = SupabaseAdminRepository()
    target = repo.get_by_username(username)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.get("role") == "super_admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The super admin already has every feature")
    _validate_features(body.allowed_features)
    repo.update_features(username, body.allowed_features)
    return {"username": username, "allowed_features": body.allowed_features}


@router.delete("/{username}")
def delete_user(username: str, current: CurrentUser = Depends(require_super_admin)) -> dict:
    repo = SupabaseAdminRepository()
    target = repo.get_by_username(username)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.get("role") == "super_admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the super admin")
    if username == current.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")
    repo.delete_user(username)
    return {"deleted": username}
