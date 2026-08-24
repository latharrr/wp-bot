from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_admin, require_feature
from app.repositories.supabase_poll_repository import SupabasePollRepository

router = APIRouter(prefix="/polls", tags=["polls"], dependencies=[Depends(require_feature("groups"))])


@router.get("")
def list_all_polls(
    group_jid: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _: str = Depends(get_current_admin),
) -> dict:
    """Cross-group poll listing -- distinct from GET /groups/{group_jid}/polls, which is
    scoped to one group's own tab in the dashboard."""
    rows, total = SupabasePollRepository().list_all_polls(group_jid, page, page_size)
    return {"total": total, "page": page, "page_size": page_size, "polls": rows}
