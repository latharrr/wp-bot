import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_admin
from app.models.api import BulkGroupActionBody
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.services.consent_service import get_consent_service

router = APIRouter(prefix="/groups", tags=["groups"])
logger = logging.getLogger(__name__)


@router.get("")
def list_groups(_: str = Depends(get_current_admin)) -> list[dict]:
    return SupabaseGroupRepository().list_groups()


@router.post("/bulk-mark-consented")
def bulk_mark_consented(body: BulkGroupActionBody, actor: str = Depends(get_current_admin)) -> dict:
    service = get_consent_service()
    for group_jid in body.group_jids:
        service.mark_group_consented(group_jid, actor)
    return {"count": len(body.group_jids)}


@router.post("/bulk-revoke-consent")
def bulk_revoke_consent(body: BulkGroupActionBody, actor: str = Depends(get_current_admin)) -> dict:
    service = get_consent_service()
    for group_jid in body.group_jids:
        service.revoke_group_consent(group_jid, actor)
    return {"count": len(body.group_jids)}


@router.post("/bulk-request-consent")
async def bulk_request_consent(body: BulkGroupActionBody, actor: str = Depends(get_current_admin)) -> dict:
    """Posts the consent-prompt message into each selected group. Sequential and per-group
    try/except on purpose: this hits the live bridge control server for every group, and one
    group being unreachable (e.g. bot no longer a member) shouldn't abort the rest of the batch."""
    service = get_consent_service()
    sent: list[str] = []
    failed: list[dict] = []
    for group_jid in body.group_jids:
        try:
            await service.request_consent(group_jid, actor)
            sent.append(group_jid)
        except Exception as exc:
            logger.exception("bulk-request-consent failed for group %s", group_jid)
            failed.append({"group_jid": group_jid, "error": str(exc)})
    return {"sent": sent, "failed": failed}


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
