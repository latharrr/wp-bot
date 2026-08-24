"""In-memory record of the bridge's connection state.

Updated exclusively by the internal /session-event webhook (app/api/internal/routes/whatsapp.py)
and read by the dashboard-facing /session/status endpoint. Process-local by design: there is only
ever one bridge subprocess per API process, same assumption the reference repo makes.
"""
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    PAIRING = "pairing"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LOGGED_OUT = "logged_out"


@dataclass
class SessionState:
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    phone_number: str | None = None
    pairing_code: str | None = None
    last_event_at: datetime | None = None
    last_error: str | None = None

    def apply_event(self, event: str, phone_number: str | None, status_code: int | None) -> None:
        self.last_event_at = datetime.now(UTC)
        if phone_number:
            self.phone_number = phone_number

        if event == "connecting":
            self.status = ConnectionStatus.CONNECTING
        elif event == "connected":
            self.status = ConnectionStatus.CONNECTED
            self.last_error = None
        elif event == "logged_out":
            self.status = ConnectionStatus.LOGGED_OUT
            self.last_error = f"logged out (code={status_code})" if status_code else "logged out"
        elif event == "disconnected":
            self.status = ConnectionStatus.DISCONNECTED
        else:
            self.last_error = f"unknown session event: {event}"


_state = SessionState()


def get_session_state() -> SessionState:
    return _state
