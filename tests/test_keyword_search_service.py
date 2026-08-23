from unittest.mock import MagicMock

import pytest

from app.services import keyword_search_service as keyword_search_module
from app.services.keyword_search_service import KeywordSearchService


@pytest.fixture
def service(monkeypatch):
    mock_repo = MagicMock()
    monkeypatch.setattr(keyword_search_module, "SupabaseKeywordRepository", lambda: mock_repo)
    return KeywordSearchService(), mock_repo


def test_check_message_for_keywords_is_case_insensitive(service):
    svc, repo = service
    message_row = {
        "message_text": "Please check the PG results",
        "group_jid": "120@g.us",
        "sender_jid": "919@s.whatsapp.net",
        "sender_name": "Alice",
        "sender_phone": "919",
        "message_id": "msg-1",
        "sent_at": "2026-08-20T00:00:00+00:00",
    }
    svc.check_message_for_keywords(["pg"], message_row)
    repo.upsert_match.assert_called_once_with(
        {
            "keyword": "pg",
            "group_jid": "120@g.us",
            "sender_jid": "919@s.whatsapp.net",
            "sender_name": "Alice",
            "sender_phone": "919",
            "message": "Please check the PG results",
            "message_id": "msg-1",
            "message_date": "2026-08-20T00:00:00+00:00",
        }
    )


def test_check_message_for_keywords_no_match_skips_upsert(service):
    svc, repo = service
    message_row = {
        "message_text": "nothing relevant here",
        "group_jid": "120@g.us",
        "sender_jid": "919@s.whatsapp.net",
        "message_id": "msg-1",
        "sent_at": "2026-08-20T00:00:00+00:00",
    }
    svc.check_message_for_keywords(["pg"], message_row)
    repo.upsert_match.assert_not_called()


def test_search_blank_keyword_short_circuits(service):
    svc, repo = service
    result = svc.search("   ")
    assert result == {"keyword": "", "results": [], "hidden_match_count": 0}
    repo.search_messages_ilike.assert_not_called()
    repo.record_watch.assert_not_called()


def test_search_backfills_records_watch_and_computes_hidden_count(service):
    svc, repo = service
    repo.search_messages_ilike.return_value = [
        {
            "message_text": "pg results are out",
            "group_jid": "120@g.us",
            "sender_jid": "919@s.whatsapp.net",
            "message_id": "msg-1",
            "sent_at": "2026-08-20T00:00:00+00:00",
        }
    ]
    repo.list_exportable_matches.return_value = [{"keyword": "pg"}]
    repo.count_all_matches.return_value = 5

    result = svc.search(" pg ")

    repo.record_watch.assert_called_once_with("pg")
    repo.upsert_match.assert_called_once()
    assert result == {"keyword": "pg", "results": [{"keyword": "pg"}], "hidden_match_count": 4}
