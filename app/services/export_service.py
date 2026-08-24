"""Builds .xlsx exports and writes the audit-log row. This is one of the two places (the
other being the dashboard "detail" queries) allowed to read exportable_contacts /
exportable_keyword_matches -- see migration 016 and supabase_group_repository /
supabase_keyword_repository for why those views exist."""
import io
from datetime import UTC, datetime

from openpyxl import Workbook

from app.models.export import ExportAuditLogEntry
from app.repositories.supabase_export_repository import SupabaseExportRepository
from app.repositories.supabase_group_repository import SupabaseGroupRepository
from app.repositories.supabase_keyword_repository import SupabaseKeywordRepository
from app.repositories.supabase_poll_repository import SupabasePollRepository


def _workbook_bytes(headers: list[str], rows: list[list]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


class ExportService:
    def __init__(self) -> None:
        self._groups = SupabaseGroupRepository()
        self._polls = SupabasePollRepository()
        self._keywords = SupabaseKeywordRepository()
        self._audit = SupabaseExportRepository()

    def export_contacts(self, group_jid: str, actor: str) -> tuple[bytes, str]:
        rows = self._groups.list_exportable_contacts(group_jid)
        content = _workbook_bytes(
            ["Name", "Phone", "Group", "Opted In At"],
            [[r.get("display_name"), r.get("phone"), r.get("group_name"), r.get("opted_in_at")] for r in rows],
        )
        filename = f"contacts_{group_jid.replace('@', '_')}_{_timestamp()}.xlsx"
        self._audit.log_export(
            ExportAuditLogEntry(actor=actor, export_type="contacts", group_jid=group_jid, row_count=len(rows), filename=filename)
        )
        return content, filename

    def export_poll(
        self, poll_message_id: str, group_jid: str, actor: str, option: str | None = None
    ) -> tuple[bytes, str]:
        group = self._groups.get_group(group_jid)
        is_consented = bool(group and group.get("consent_status") == "consented")

        if is_consented:
            rows = self._polls.get_voter_breakdown(poll_message_id)
            if option:
                rows = [r for r in rows if option in (r.get("selected_options") or [])]
            content = _workbook_bytes(
                ["Voter Name", "Phone", "Selected Options", "Voted At"],
                [
                    [r.get("voter_name"), r.get("voter_phone"), ", ".join(r.get("selected_options") or []), r.get("last_vote_timestamp")]
                    for r in rows
                ],
            )
            row_count = len(rows)
        else:
            aggregate = self._polls.get_vote_aggregate(poll_message_id)
            if option:
                aggregate = {option: aggregate.get(option, 0)}
            content = _workbook_bytes(["Option", "Vote Count"], [[k, v] for k, v in aggregate.items()])
            row_count = sum(aggregate.values())

        option_suffix = f"_{option}" if option else ""
        filename = f"poll_{poll_message_id.replace('@', '_')}{option_suffix}_{_timestamp()}.xlsx"
        self._audit.log_export(
            ExportAuditLogEntry(actor=actor, export_type="poll", group_jid=group_jid, row_count=row_count, filename=filename)
        )
        return content, filename

    def export_keyword_matches(self, keyword: str, actor: str) -> tuple[bytes, str]:
        rows = self._keywords.list_exportable_matches(keyword)
        content = _workbook_bytes(
            ["Keyword", "Group", "Sender Name", "Phone", "Message", "Date"],
            [
                [r.get("keyword"), r.get("group_name"), r.get("sender_name"), r.get("sender_phone"), r.get("message"), r.get("message_date")]
                for r in rows
            ],
        )
        filename = f"keyword_{keyword}_{_timestamp()}.xlsx"
        self._audit.log_export(
            ExportAuditLogEntry(actor=actor, export_type="keyword", keyword=keyword, row_count=len(rows), filename=filename)
        )
        return content, filename


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def get_export_service() -> ExportService:
    return ExportService()
