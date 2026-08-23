from app.services.whatsapp_session_state import ConnectionStatus, SessionState


def test_connecting_event_sets_status():
    state = SessionState()
    state.apply_event("connecting", None, None)
    assert state.status == ConnectionStatus.CONNECTING


def test_connected_event_clears_prior_error_and_sets_phone():
    state = SessionState(last_error="boom")
    state.apply_event("connected", "919876543210", None)
    assert state.status == ConnectionStatus.CONNECTED
    assert state.phone_number == "919876543210"
    assert state.last_error is None


def test_logged_out_event_records_status_code_in_error():
    state = SessionState()
    state.apply_event("logged_out", None, 401)
    assert state.status == ConnectionStatus.LOGGED_OUT
    assert "401" in state.last_error


def test_disconnected_event_sets_status_without_touching_error():
    state = SessionState(last_error="previous issue")
    state.apply_event("disconnected", None, None)
    assert state.status == ConnectionStatus.DISCONNECTED
    assert state.last_error == "previous issue"


def test_unknown_event_records_error():
    state = SessionState()
    state.apply_event("mystery", None, None)
    assert state.last_error == "unknown session event: mystery"


def test_phone_number_only_updated_when_provided():
    state = SessionState(phone_number="919000000000")
    state.apply_event("connecting", None, None)
    assert state.phone_number == "919000000000"
