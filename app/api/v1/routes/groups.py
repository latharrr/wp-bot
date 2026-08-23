from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_admin
from app.repositories.supabase_group_repository import SupabaseGroupRepository

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("")
def list_groups(_: str = Depends(get_current_admin)) -> list[dict]:
    return SupabaseGroupRepository().list_groups()


@router.get("/{group_jid}")
def get_group(group_jid: str, _: str = Depends(get_current_admin)) -> dict:
    group = SupabaseGroupRepository().get_group(group_jid)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@router.get("/{group_jid}/members")
def list_members(group_jid: str, _: str = Depends(get_current_admin)) -> list[dict]:
    """Full member list for the operator's own consent-management UI -- distinct from the
    consent-gated exportable_contacts view (migration 016): this is for the account operator to
    see who's in their own group and manually opt someone in, not an export of identifying data."""
    return SupabaseGroupRepository().list_members(group_jid)
