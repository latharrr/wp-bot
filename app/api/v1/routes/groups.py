import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import get_current_admin, require_feature
from app.models.api import BulkGroupActionBody
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.services.backfill_service import get_backfill_service
from app.services.consent_service import get_consent_service

logger = logging.getLogger(__name__)

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
    _: str = Depends(get_current_admin),
) -> dict:
    """Manually triggers WhatsApp's on-demand history sync to pull messages older than anything
    currently recorded for one group -- pages backward in the background (see BackfillService)
    for as long as WhatsApp keeps returning more, not a guarantee of reaching the group's full
    history since creation, just as far back as WhatsApp's own servers still have available.

    Open to any user with the 'groups' feature (not super_admin-only anymore), but deliberately
    restricted to exactly one group per request, with a system-wide lock so only one backfill is
    ever in flight at a time account-wide -- otherwise several users could each kick one off
    concurrently, which is exactly the kind of concentrated sync traffic this stays conservative
    about (see the README's ban-risk notes)."""
    if len(body.group_jids) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one group can be backfilled at a time.",
        )
    group_jid = body.group_jids[0]

    groups_repo = SupabaseGroupRepository()
    try:
        running = groups_repo.get_running_backfill()
    except Exception:
        # Most likely migration 019_add_backfill_status_to_groups.sql hasn't been applied yet --
        # fall back to allowing the request rather than breaking backfill entirely over a
        # best-effort safety check (see BackfillService._record_status for the same tradeoff).
        logger.exception("Could not check for an in-flight backfill -- has migration 019 been applied?")
        running = None
    if running and running["group_jid"] != group_jid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A backfill is already running for '{running.get('group_name') or running['group_jid']}' -- "
                "wait for it to finish before starting another."
            ),
        )

    service = get_backfill_service()
    anchor = service.anchor_for_group(group_jid)
    if not anchor:
        return {"queued": [], "skipped": [group_jid]}
    background_tasks.add_task(service.run, [group_jid])
    return {"queued": [group_jid], "skipped": []}


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
