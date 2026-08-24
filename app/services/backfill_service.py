import logging
from datetime import datetime

from app.core.bridge_control_client import get_bridge_control_client
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.repositories.supabase_keyword_repository import SupabaseKeywordRepository

logger = logging.getLogger(__name__)


class BackfillService:
    """Drives the manual, super_admin-only deep history backfill for a chosen set of groups.
    Deliberately awaits each group's backfill fully before starting the next one -- never fires
    multiple groups' on-demand history syncs at once, no matter how many are selected -- since
    that's exactly the kind of concentrated sync traffic the bridge otherwise avoids to reduce
    ban risk on the live paired number (see backfill.ts and the README's ban-risk notes)."""

    def __init__(self) -> None:
        self._groups = SupabaseGroupRepository()
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

    def _record_status(self, fn, *args, **kwargs) -> None:
        """Status bookkeeping is best-effort -- if migration 019 hasn't been applied yet (the
        backfill_* columns don't exist), the actual on-demand history sync should still run;
        only the Groups page's progress display degrades."""
        try:
            fn(*args, **kwargs)
        except Exception:
            logger.exception(
                "Could not persist backfill status -- has "
                "supabase/migrations/019_add_backfill_status_to_groups.sql been applied?"
            )

    async def run(self, group_jids: list[str]) -> None:
        client = get_bridge_control_client()
        for group_jid in group_jids:
            anchor = self.anchor_for_group(group_jid)
            if not anchor:
                logger.warning("Skipping backfill for %s: no messages recorded yet to anchor from", group_jid)
                continue
            self._record_status(self._groups.mark_backfill_started, group_jid)
            try:
                result = await client.backfill_history(group_jid=group_jid, **anchor)
                # The oldest message on record *after* the run -- i.e. how far back this group's
                # history now actually goes, shown on the Groups page as the backfill's "till date".
                oldest = self._keywords.get_oldest_message(group_jid)
                self._record_status(
                    self._groups.mark_backfill_finished,
                    group_jid,
                    pages_fetched=result.get("pagesFetched", 0),
                    messages_stored=result.get("messagesStored", 0),
                    stopped_reason=result.get("stoppedReason", "unknown"),
                    oldest_message_at=oldest["sent_at"] if oldest else None,
                )
                logger.info("Backfill for %s finished: %s", group_jid, result)
            except Exception:
                logger.exception("Backfill for %s failed", group_jid)
                self._record_status(self._groups.mark_backfill_failed, group_jid)


def get_backfill_service() -> BackfillService:
    return BackfillService()
