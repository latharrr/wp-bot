from app.core import rate_limit


def setup_function():
    rate_limit._failed_attempts.clear()


def test_not_locked_out_initially():
    assert rate_limit.is_locked_out("alice") is False


def test_locks_out_after_max_attempts():
    for _ in range(rate_limit.MAX_ATTEMPTS):
        rate_limit.record_failed_attempt("alice")
    assert rate_limit.is_locked_out("alice") is True


def test_locked_out_key_does_not_affect_other_keys():
    for _ in range(rate_limit.MAX_ATTEMPTS):
        rate_limit.record_failed_attempt("alice")
    assert rate_limit.is_locked_out("bob") is False


def test_clear_attempts_lifts_lockout():
    for _ in range(rate_limit.MAX_ATTEMPTS):
        rate_limit.record_failed_attempt("alice")
    rate_limit.clear_attempts("alice")
    assert rate_limit.is_locked_out("alice") is False


def test_one_below_threshold_not_locked_out():
    for _ in range(rate_limit.MAX_ATTEMPTS - 1):
        rate_limit.record_failed_attempt("alice")
    assert rate_limit.is_locked_out("alice") is False
