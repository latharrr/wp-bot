from fastapi import APIRouter, Depends

from app.api.deps import get_current_admin, require_feature
from app.repositories.supabase_export_repository import SupabaseExportRepository

router = APIRouter(prefix="/export-log", tags=["exports"], dependencies=[Depends(require_feature("export_log"))])


@router.get("")
def list_export_log(_: str = Depends(get_current_admin)) -> list[dict]:
    return SupabaseExportRepository().list_recent()
