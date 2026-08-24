from datetime import date
from unittest.mock import MagicMock

import pytest

from app.models.whatsapp import PollVotePayload
from app.services import whatsapp_poll_ingestion_service as ingestion_module
from app.services.whatsapp_poll_ingestion_service import WhatsappPollIngestionService


@pytest.fixture
def service(monkeypatch):
    mock_polls = MagicMock()
    mock_toggles = MagicMock()
    monkeypatch.setattr(ingestion_module, "SupabasePollRepository", lambda: mock_polls)
    monkeypatch.setattr(ingestion_module, "SupabaseFeatureToggleRepository", lambda: mock_toggles)
    mock_polls.insert_vote_event_if_new.return_value = True
    mock_toggles.is_enabled.return_value = True
    mock_polls.fetch_user_history.return_value = []
    svc = WhatsappPollIngestionService()
    return svc, mock_polls, mock_toggles


def _payload(**overrides) -> PollVotePayload:
    defaults = {
        "dedupe_key": "dk-1",
        "group_jid": "120@g.us",
        "poll_message_id": "poll-1",
        "poll_title": "Will you buy?",
        "poll_options": ["Yes", "No"],
        "voter_jid": "919@s.whatsapp.net",
        "voter_phone": "919999999999",
        "voter_name": "Alice",
        "selected_options": ["Yes"],
        "vote_timestamp_ms": 1755960000000,
    }
    defaults.update(overrides)
    return PollVotePayload(**defaults)


def test_yes_vote_on_binary_poll_gets_scored(service):
    svc, polls, _toggles = service
    svc.handle_poll_vote(_payload())
    polls.upsert_predictions.assert_called_once()
    rows = polls.upsert_predictions.call_args.args[0]
    assert rows[0]["mobile"] == "919999999999"
    assert rows[0]["vote"] == "yes"
    assert rows[0]["source_filename"] == "whatsapp:poll-1"
    assert 0.0 <= rows[0]["prediction_score"] <= 100.0


def test_no_vote_is_not_scored(service):
    svc, polls, _toggles = service
    svc.handle_poll_vote(_payload(selected_options=["No"]))
    polls.upsert_predictions.assert_not_called()


def test_non_binary_poll_is_not_scored(service):
    svc, polls, _toggles = service
    svc.handle_poll_vote(_payload(poll_options=["2BHK", "3BHK", "Studio"], selected_options=["2BHK"]))
    polls.upsert_predictions.assert_not_called()


def test_vote_without_phone_is_not_scored(service):
    svc, polls, _toggles = service
    svc.handle_poll_vote(_payload(voter_phone=None))
    polls.upsert_predictions.assert_not_called()


def test_scoring_disabled_by_toggle_skips_scoring_but_still_stores_vote(service):
    svc, polls, toggles = service
    toggles.is_enabled.return_value = False
    svc.handle_poll_vote(_payload())
    polls.upsert_predictions.assert_not_called()
    polls.upsert_vote_snapshot.assert_called_once()


def test_duplicate_vote_event_skips_snapshot_and_scoring(service):
    svc, polls, _toggles = service
    polls.insert_vote_event_if_new.return_value = False
    svc.handle_poll_vote(_payload())
    polls.upsert_vote_snapshot.assert_not_called()
    polls.upsert_predictions.assert_not_called()


def test_vote_event_and_snapshot_carry_normalized_vote(service):
    svc, polls, _toggles = service
    svc.handle_poll_vote(_payload())
    event_payload = polls.insert_vote_event_if_new.call_args.args[1]
    snapshot_payload = polls.upsert_vote_snapshot.call_args.args[0]
    assert event_payload["normalized_vote"] == 1
    assert snapshot_payload["normalized_vote"] == 1


def test_score_uses_fetched_history(service):
    svc, polls, _toggles = service
    polls.fetch_user_history.return_value = [
        {"mobile": "919999999999", "total_purchases": 3, "last_purchase_date": date(2025, 8, 10), "total_yes_votes": 0}
    ]
    svc.handle_poll_vote(_payload())
    polls.fetch_user_history.assert_called_once_with(["919999999999"])
    rows = polls.upsert_predictions.call_args.args[0]
    assert rows[0]["prediction_score"] == 70.0
