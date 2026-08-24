from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_admin, require_feature
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.repositories.supabase_keyword_repository import SupabaseKeywordRepository

router = APIRouter(
    prefix="/groups/{group_jid}/messages", tags=["messages"], dependencies=[Depends(require_feature("groups"))]
)


@router.get("")
def list_messages(
    group_jid: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _: str = Depends(get_current_admin),
) -> dict:
    """The group conversation monitor -- group-consent-only gate, same precedent as poll voter
    breakdowns (see SupabaseKeywordRepository.list_matches_in_consented_groups): the group's own
    consent authorizes viewing its content, no per-member opt-in required."""
    group = SupabaseGroupRepository().get_group(group_jid)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    keywords = SupabaseKeywordRepository()
    if group.get("consent_status") != "consented":
        total = keywords.count_messages_for_group(group_jid)
        return {"exportable": False, "total": total, "page": page, "page_size": page_size, "messages": []}

    rows, total = keywords.list_messages_for_group(group_jid, page, page_size)
    return {"exportable": True, "total": total, "page": page, "page_size": page_size, "messages": rows}
