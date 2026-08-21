"""Client for the bridge's own tiny localhost control server.

Used only for operator-initiated actions that need to reach into the live WhatsApp session,
e.g. posting a consent-prompt message into a group. Separate trust boundary from the
internal webhook direction (bridge -> Python): this is Python -> bridge, guarded by its own
shared-secret header so a compromised dashboard session still can't hit it without the secret.
"""
import httpx

from app.core.config import get_settings


class BridgeControlClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.whatsapp_bridge_control_url
        self._token = settings.whatsapp_bridge_control_token

    async def send_message(self, group_jid: str, text: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self._base_url}/send-message",
                json={"group_jid": group_jid, "text": text},
                headers={"x-control-token": self._token},
            )
            response.raise_for_status()
            return response.json()["message_id"]

    async def refresh_groups(self) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self._base_url}/refresh-groups",
                headers={"x-control-token": self._token},
            )
            response.raise_for_status()


def get_bridge_control_client() -> BridgeControlClient:
    return BridgeControlClient()
