"""Client for the bridge's own tiny localhost control server -- used for operator-initiated
actions that need to reach into the live WhatsApp session (currently: a real logout). Separate
trust boundary from the internal webhook direction (bridge -> Python): this is Python -> bridge,
guarded by its own shared-secret header so a compromised dashboard session still can't hit it
without the secret."""
import httpx

from app.core.config import get_settings


class BridgeControlClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.whatsapp_bridge_control_url
        self._token = settings.whatsapp_bridge_control_token

    async def logout(self) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self._base_url}/logout",
                headers={"x-control-token": self._token},
            )
            response.raise_for_status()

    async def backfill_history(
        self,
        group_jid: str,
        anchor_message_id: str,
        anchor_participant: str | None,
        anchor_timestamp_sec: float,
    ) -> dict:
        """Blocks until the bridge finishes paging backward through one group's on-demand history
        sync -- deliberately no timeout, since a deep backfill can legitimately take minutes and
        BackfillService.run awaits this once per group, sequentially, so the next group never
        starts until this one is fully done."""
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{self._base_url}/backfill-history",
                headers={"x-control-token": self._token},
                json={
                    "group_jid": group_jid,
                    "anchor_message_id": anchor_message_id,
                    "anchor_participant": anchor_participant,
                    "anchor_timestamp_sec": anchor_timestamp_sec,
                },
            )
            response.raise_for_status()
            return response.json()


def get_bridge_control_client() -> BridgeControlClient:
    return BridgeControlClient()
