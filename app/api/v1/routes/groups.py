from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import (
    CurrentUser,
    get_current_admin,
    require_feature,
    require_super_admin,
)
from app.models.api import BulkGroupActionBody
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.services.backfill_service import get_backfill_service
from app.services.consent_service import get_consent_service

router = APIRouter(prefix="/groups", tags=["groups"], dependencies=[Depends(require_feature("groups"))])


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


@router.post("/backfill-history")
def backfill_history(
    body: BulkGroupActionBody,
    background_tasks: BackgroundTasks,
    _: CurrentUser = Depends(require_super_admin),
) -> dict:
    """Manually triggers WhatsApp's on-demand history sync to pull messages older than anything
    currently recorded, for each selected group in turn -- one group fully at a time in the
    background (see BackfillService). Not a guarantee of reaching a group's full history since
    creation, just as far back as WhatsApp's own servers still have available. Deliberately a
    manual, super_admin-only action rather than an automatic bulk job -- see the README's
    consent-model/ban-risk notes."""
    service = get_backfill_service()
    anchors = {jid: service.anchor_for_group(jid) for jid in body.group_jids}
    queued = [jid for jid, anchor in anchors.items() if anchor is not None]
    skipped = [jid for jid, anchor in anchors.items() if anchor is None]
    background_tasks.add_task(service.run, queued)
    return {"queued": queued, "skipped": skipped}


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
