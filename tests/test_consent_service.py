from unittest.mock import MagicMock

import pytest

from app.services import consent_service as consent_service_module
from app.services.consent_service import ConsentService


@pytest.fixture
def service(monkeypatch):
    mock_groups = MagicMock()
    mock_consent = MagicMock()
    monkeypatch.setattr(consent_service_module, "SupabaseGroupRepository", lambda: mock_groups)
    monkeypatch.setattr(consent_service_module, "SupabaseConsentRepository", lambda: mock_consent)
    svc = ConsentService()
    return svc, mock_groups, mock_consent


def test_handle_reply_ignored_without_reply_id_or_phone(service):
    svc, _groups, consent = service
    assert svc.handle_reply("120@g.us", None, "9198765") is False
    assert svc.handle_reply("120@g.us", "msg-1", None) is False
    consent.get_active_prompt_by_message_id.assert_not_called()


def test_handle_reply_ignored_when_no_active_prompt(service):
    svc, _groups, consent = service
    consent.get_active_prompt_by_message_id.return_value = None
    assert svc.handle_reply("120@g.us", "msg-1", "9198765") is False
    consent.record_opt_in.assert_not_called()


def test_handle_reply_ignored_when_prompt_belongs_to_different_group(service):
    svc, _groups, consent = service
    consent.get_active_prompt_by_message_id.return_value = {"group_jid": "other@g.us"}
    assert svc.handle_reply("120@g.us", "msg-1", "9198765") is False
    consent.record_opt_in.assert_not_called()


def test_handle_reply_records_opt_in_when_prompt_matches(service):
    svc, _groups, consent = service
    consent.get_active_prompt_by_message_id.return_value = {"group_jid": "120@g.us"}
    assert svc.handle_reply("120@g.us", "msg-1", "9198765") is True
    consent.record_opt_in.assert_called_once()
    record = consent.record_opt_in.call_args.args[0]
    assert record.group_jid == "120@g.us"
    assert record.member_phone == "9198765"
    assert record.opt_in_method == "reply"
    assert record.opt_in_message_id == "msg-1"


def test_handle_reaction_records_opt_in_when_prompt_matches(service):
    svc, _groups, consent = service
    consent.get_active_prompt_by_message_id.return_value = {"group_jid": "120@g.us"}
    assert svc.handle_reaction("120@g.us", "msg-1", "9198765") is True
    record = consent.record_opt_in.call_args.args[0]
    assert record.opt_in_method == "reaction"


def test_handle_reaction_ignored_without_reactor_phone(service):
    svc, _groups, consent = service
    assert svc.handle_reaction("120@g.us", "msg-1", None) is False
    consent.get_active_prompt_by_message_id.assert_not_called()


def test_mark_group_consented_delegates_to_repository(service):
    svc, groups, _consent = service
    svc.mark_group_consented("120@g.us", "operator")
    groups.set_consent_status.assert_called_once_with("120@g.us", "consented", "operator")


def test_revoke_group_consent_delegates_to_repository(service):
    svc, groups, _consent = service
    svc.revoke_group_consent("120@g.us", "operator")
    groups.set_consent_status.assert_called_once_with("120@g.us", "revoked", "operator")
