import logging
from datetime import datetime

from app.core.bridge_control_client import get_bridge_control_client
from app.repositories.supabase_keyword_repository import SupabaseKeywordRepository

logger = logging.getLogger(__name__)


class BackfillService:
    """Drives the manual, super_admin-only deep history backfill for a chosen set of groups.
    Deliberately awaits each group's backfill fully before starting the next one -- never fires
    multiple groups' on-demand history syncs at once, no matter how many are selected -- since
    that's exactly the kind of concentrated sync traffic the bridge otherwise avoids to reduce
    ban risk on the live paired number (see backfill.ts and the README's ban-risk notes)."""

    def __init__(self) -> None:
        self._keywords = SupabaseKeywordRepository()

    def anchor_for_group(self, group_jid: str) -> dict | None:
        """A group needs at least one message already on record to page backward from -- there's
        no anchor to start a fresh on-demand history request from otherwise."""
        oldest = self._keywords.get_oldest_message(group_jid)
        if not oldest:
            return None
        return {
            "anchor_message_id": oldest["message_id"],
            "anchor_participant": oldest["sender_jid"],
            "anchor_timestamp_sec": datetime.fromisoformat(oldest["sent_at"]).timestamp(),
        }

    async def run(self, group_jids: list[str]) -> None:
        client = get_bridge_control_client()
        for group_jid in group_jids:
            anchor = self.anchor_for_group(group_jid)
            if not anchor:
                logger.warning("Skipping backfill for %s: no messages recorded yet to anchor from", group_jid)
                continue
            try:
                result = await client.backfill_history(group_jid=group_jid, **anchor)
                logger.info("Backfill for %s finished: %s", group_jid, result)
            except Exception:
                logger.exception("Backfill for %s failed", group_jid)


def get_backfill_service() -> BackfillService:
    return BackfillService()
