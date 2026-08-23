from fastapi import APIRouter, Depends

from app.api.deps import get_current_admin, require_feature
from app.models.api import BulkOptInBody, ManualOptInBody
from app.services.consent_service import get_consent_service

router = APIRouter(
    prefix="/groups/{group_jid}/consent", tags=["consent"], dependencies=[Depends(require_feature("groups"))]
)


@router.get("/members")
def list_member_consent(group_jid: str, _: str = Depends(get_current_admin)) -> list[dict]:
    return get_consent_service().get_member_consent_progress(group_jid)


@router.post("/mark-consented")
def mark_consented(group_jid: str, actor: str = Depends(get_current_admin)) -> dict:
    get_consent_service().mark_group_consented(group_jid, actor)
    return {"group_jid": group_jid, "consent_status": "consented"}


@router.post("/revoke")
def revoke(group_jid: str, actor: str = Depends(get_current_admin)) -> dict:
    get_consent_service().revoke_group_consent(group_jid, actor)
    return {"group_jid": group_jid, "consent_status": "revoked"}


@router.post("/members/{phone}/opt-in")
def manual_opt_in(group_jid: str, phone: str, body: ManualOptInBody, _: str = Depends(get_current_admin)) -> dict:
    get_consent_service().manual_opt_in(group_jid, phone)
    return {"group_jid": group_jid, "phone": phone, "opted_in": True}


@router.post("/members/{phone}/opt-out")
def manual_opt_out(group_jid: str, phone: str, _: str = Depends(get_current_admin)) -> dict:
    get_consent_service().manual_opt_out(group_jid, phone)
    return {"group_jid": group_jid, "phone": phone, "opted_in": False}


@router.post("/members/bulk-opt-in")
def bulk_manual_opt_in(group_jid: str, body: BulkOptInBody, _: str = Depends(get_current_admin)) -> dict:
    count = get_consent_service().bulk_manual_opt_in(group_jid, body.phones)
    return {"group_jid": group_jid, "opted_in_count": count}
