from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import get_current_admin, require_feature
from app.services.export_service import get_export_service
from app.services.keyword_search_service import get_keyword_search_service

router = APIRouter(prefix="/keywords", tags=["keywords"], dependencies=[Depends(require_feature("keyword_search"))])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/search")
def search(q: str = Query(..., min_length=1), _: str = Depends(get_current_admin)) -> dict:
    return get_keyword_search_service().search(q)


@router.get("/search/export")
def export_search(q: str = Query(..., min_length=1), actor: str = Depends(get_current_admin)) -> Response:
    get_keyword_search_service().search(q)  # ensure keyword_match is backfilled before export
    content, filename = get_export_service().export_keyword_matches(q, actor)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/recent")
def recent(_: str = Depends(get_current_admin)) -> list[dict]:
    return get_keyword_search_service().recent_searches()
