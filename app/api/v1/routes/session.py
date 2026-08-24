from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_admin, require_feature
from app.core.bridge_process import get_bridge_manager
from app.models.api import PairingCodeRequest, PairingCodeResponse, QrCodeResponse
from app.services.whatsapp_session_state import get_session_state

router = APIRouter(prefix="/session", tags=["session"], dependencies=[Depends(require_feature("connection"))])


@router.get("/status")
def get_status(_: str = Depends(get_current_admin)) -> dict:
    state = get_session_state()
    return {
        "status": state.status.value,
        "phone_number": state.phone_number,
        # A fresh, never-paired bridge sits in "connecting" indefinitely (it never requests a
        # pairing code on its own), so gating this on disconnected/logged_out only left no way
        # to pair on first run.
        "pairing_required": state.status.value != "connected",
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


@router.post("/qr-login", response_model=QrCodeResponse)
async def start_qr_login(_: str = Depends(get_current_admin)) -> QrCodeResponse:
    """Resets any existing session and starts a fresh QR-code login -- see start_qr_session's
    docstring for why this is the recommended path over /pairing-code."""
    try:
        data_url = await get_bridge_manager().start_qr_session()
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    qr = get_bridge_manager().get_qr_code()
    return QrCodeResponse(qr_data_url=data_url, generated_at=qr["generated_at"] if qr else 0)


@router.get("/qr-code", response_model=QrCodeResponse)
def get_qr_code(_: str = Depends(get_current_admin)) -> QrCodeResponse:
    """Polled by the dashboard while waiting to scan -- the QR rotates roughly every 20s."""
    qr = get_bridge_manager().get_qr_code()
    if not qr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No QR code available yet")
    return QrCodeResponse(**qr)


@router.post("/disconnect")
async def disconnect(_: str = Depends(get_current_admin)) -> dict:
    """Properly unlinks the device from WhatsApp (not just stopping our local process) and
    clears the local session -- a fresh QR/pairing is required to reconnect afterward."""
    await get_bridge_manager().disconnect()
    return {"status": "disconnected"}
