import re

PASS_THRESHOLD = 0.8


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    return re.sub(r"\s+", " ", lowered)


def keyword_overlap_score(actual: str, expected: str) -> float:
    expected_words = {word for word in re.findall(r"\w+", normalize_text(expected)) if word}
    if not expected_words:
        return 0.0

    actual_words = set(re.findall(r"\w+", normalize_text(actual)))
    overlap = expected_words & actual_words
    return len(overlap) / len(expected_words)


def score_output(actual: str, expected: str) -> tuple[float, bool]:
    if actual == expected:
        return 1.0, True

    if normalize_text(actual) == normalize_text(expected):
        return 1.0, True

    overlap = keyword_overlap_score(actual, expected)
    passed = overlap >= PASS_THRESHOLD
    return overlap, passed
