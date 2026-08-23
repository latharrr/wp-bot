from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_current_admin, require_feature
from app.services.poll_scoring_service import get_poll_scoring_service

router = APIRouter(prefix="/polls", tags=["scoring"], dependencies=[Depends(require_feature("csv_scoring"))])


@router.post("/score")
async def score_poll_csv(file: UploadFile, _: str = Depends(get_current_admin)) -> Response:
    raw_bytes = await file.read()
    try:
        result = get_poll_scoring_service().score_csv(raw_bytes, source_filename=file.filename or "upload.csv")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(
        content=result["scored_csv"],
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="scored.csv"',
            "X-Above-Threshold-Count": str(result["above_threshold_count"]),
            "X-Row-Count": str(result["row_count"]),
        },
    )
