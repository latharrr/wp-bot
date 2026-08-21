from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_admin
from app.core.bridge_process import get_bridge_manager
from app.models.api import PairingCodeRequest, PairingCodeResponse
from app.services.whatsapp_session_state import get_session_state

router = APIRouter(prefix="/session", tags=["session"])


@router.get("/status")
def get_status(_: str = Depends(get_current_admin)) -> dict:
    state = get_session_state()
    return {
        "status": state.status.value,
        "phone_number": state.phone_number,
        "pairing_required": state.status.value in ("disconnected", "logged_out"),
        "last_event_at": state.last_event_at,
        "last_error": state.last_error,
    }


@router.post("/pairing-code", response_model=PairingCodeResponse)
async def request_pairing_code(body: PairingCodeRequest, _: str = Depends(get_current_admin)) -> PairingCodeResponse:
    try:
        code = await get_bridge_manager().request_pairing_code(body.phone_number)
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    return PairingCodeResponse(pairing_code=code)
