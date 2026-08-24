from app.services.vote_normalization import normalize_vote


def test_recognizes_yes_no_pair():
    assert normalize_vote(["Yes", "No"], ["Yes"]) == 1
    assert normalize_vote(["Yes", "No"], ["No"]) == 0


def test_recognizes_alternate_positive_negative_phrasings():
    assert normalize_vote(["I will buy", "Not interested"], ["I will buy"]) == 1
    assert normalize_vote(["Count me in", "Skip"], ["Skip"]) == 0


def test_case_and_punctuation_insensitive():
    assert normalize_vote(["YES!", "no."], ["yes!"]) == 1


def test_returns_none_for_non_binary_poll():
    assert normalize_vote(["2BHK", "3BHK", "Studio"], ["2BHK"]) is None


def test_returns_none_when_options_dont_map_to_known_tokens():
    assert normalize_vote(["Option A", "Option B"], ["Option A"]) is None


def test_returns_none_when_multiple_options_selected():
    assert normalize_vote(["Yes", "No"], ["Yes", "No"]) is None


def test_returns_none_when_no_option_selected():
    assert normalize_vote(["Yes", "No"], []) is None


def test_returns_none_when_both_options_map_to_same_side():
    assert normalize_vote(["Yes", "Interested"], ["Yes"]) is None
