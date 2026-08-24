from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, require_super_admin
from app.repositories.supabase_feature_toggle_repository import (
    SupabaseFeatureToggleRepository,
)

router = APIRouter(prefix="/feature-toggles", tags=["feature-toggles"], dependencies=[Depends(require_super_admin)])


@router.get("")
def list_toggles(_: CurrentUser = Depends(require_super_admin)) -> list[dict]:
    return SupabaseFeatureToggleRepository().list_all()


@router.post("/{key}/enable")
def enable_toggle(key: str, _: CurrentUser = Depends(require_super_admin)) -> dict:
    SupabaseFeatureToggleRepository().set_enabled(key, True)
    return {"key": key, "enabled": True}


@router.post("/{key}/disable")
def disable_toggle(key: str, _: CurrentUser = Depends(require_super_admin)) -> dict:
    SupabaseFeatureToggleRepository().set_enabled(key, False)
    return {"key": key, "enabled": False}
