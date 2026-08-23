from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.deps import get_current_admin, require_feature
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.services.export_service import get_export_service

router = APIRouter(
    prefix="/groups/{group_jid}/contacts", tags=["contacts"], dependencies=[Depends(require_feature("groups"))]
)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("")
def list_contacts(group_jid: str, _: str = Depends(get_current_admin)) -> dict:
    groups = SupabaseGroupRepository()
    group = groups.get_group(group_jid)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if group.get("consent_status") != "consented":
        return {"member_count": group.get("member_count", 0), "exportable": False, "members": []}

    return {"member_count": group.get("member_count", 0), "exportable": True, "members": groups.list_exportable_contacts(group_jid)}


@router.get("/export")
def export_contacts(group_jid: str, actor: str = Depends(get_current_admin)) -> Response:
    group = SupabaseGroupRepository().get_group(group_jid)
    if not group or group.get("consent_status") != "consented":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This group has not been marked consented")

    content, filename = get_export_service().export_contacts(group_jid, actor)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
