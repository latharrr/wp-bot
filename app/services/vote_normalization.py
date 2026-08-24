"""Ported from poison-br09/whatsapp-propensity-scoring: maps a poll's two options to a binary
yes/no intent (when recognizable) so a live vote can be scored automatically, the same way a
CSV row is, without waiting for a human to export/upload anything."""
import re

POSITIVE_TOKENS = {
    "yes",
    "y",
    "interested",
    "buy",
    "will buy",
    "i will buy",
    "want",
    "count me in",
    "in",
    "go ahead",
    "order",
}
NEGATIVE_TOKENS = {
    "no",
    "n",
    "not interested",
    "wont buy",
    "will not buy",
    "dont want",
    "do not want",
    "skip",
    "not now",
    "out",
}


def _canonicalize(value: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    return re.sub(r"\s+", " ", compact)


def _infer_binary_mapping(poll_options: list[str]) -> dict[str, int] | None:
    normalized_options = [_canonicalize(option) for option in poll_options if _canonicalize(option)]
    if len(normalized_options) != 2:
        return None

    classified: dict[str, int] = {}
    for option in normalized_options:
        if option in POSITIVE_TOKENS:
            classified[option] = 1
        elif option in NEGATIVE_TOKENS:
            classified[option] = 0
        else:
            return None

    if set(classified.values()) != {0, 1}:
        return None
    return classified


def normalize_vote(poll_options: list[str], selected_options: list[str]) -> int | None:
    """Returns 1 (yes-like), 0 (no-like), or None if the poll isn't a recognizable binary
    yes/no pair, or the voter picked more/less than exactly one option."""
    mapping = _infer_binary_mapping(poll_options)
    if not mapping or len(selected_options) != 1:
        return None
    return mapping.get(_canonicalize(selected_options[0]))
