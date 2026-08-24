from dataclasses import dataclass


@dataclass
class ExportAuditLogEntry:
    actor: str
    export_type: str  # contacts | poll | keyword
    row_count: int
    filename: str
    group_jid: str | None = None
    keyword: str | None = None

    def to_supabase_payload(self) -> dict:
        return {
            "actor": self.actor,
            "export_type": self.export_type,
            "row_count": self.row_count,
            "filename": self.filename,
            "group_jid": self.group_jid,
            "keyword": self.keyword,
        }
