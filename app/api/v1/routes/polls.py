from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.api.deps import get_current_admin, require_feature
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.repositories.supabase_poll_repository import SupabasePollRepository
from app.services.export_service import get_export_service

router = APIRouter(
    prefix="/groups/{group_jid}/polls", tags=["polls"], dependencies=[Depends(require_feature("groups"))]
)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("")
def list_polls(group_jid: str, _: str = Depends(get_current_admin)) -> list[dict]:
    return SupabasePollRepository().list_polls_for_group(group_jid)


@router.get("/{poll_message_id}")
def get_poll_detail(group_jid: str, poll_message_id: str, _: str = Depends(get_current_admin)) -> dict:
    polls = SupabasePollRepository()
    poll = polls.get_poll(poll_message_id)
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    group = SupabaseGroupRepository().get_group(group_jid)
    is_consented = bool(group and group.get("consent_status") == "consented")

    if is_consented:
        return {**poll, "exportable": True, "voters": polls.get_voter_breakdown(poll_message_id)}
    return {**poll, "exportable": False, "aggregate_counts": polls.get_vote_aggregate(poll_message_id)}


@router.get("/{poll_message_id}/export")
def export_poll(
    group_jid: str,
    poll_message_id: str,
    option: Optional[str] = Query(default=None, description="Limit the export to voters who picked this option"),
    actor: str = Depends(get_current_admin),
) -> Response:
    content, filename = get_export_service().export_poll(poll_message_id, group_jid, actor, option)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
