import asyncio

from app.services.scorer import (
    keyword_overlap_score,
    normalize_text,
    score_output,
    score_output_with_hits,
)


def test_normalize_text():
    assert normalize_text("  Hello   World  ") == "hello world"


def test_exact_match():
    score, passed = score_output("Paris", "Paris")
    assert score == 1.0
    assert passed is True


def test_score_output_with_hits_exact():
    score, passed, hits = score_output_with_hits("Paris", "Paris")
    assert score == 1.0
    assert passed is True
    assert hits == ["exact_match"]


def test_normalized_match():
    score, passed = score_output("  paris ", "Paris")
    assert score == 1.0
    assert passed is True


def test_keyword_overlap_pass():
    score, passed = score_output(
        "Hypertext Transfer Protocol",
        "Hypertext Transfer Protocol",
    )
    assert score == 1.0
    assert passed is True


def test_keyword_overlap_partial():
    overlap = keyword_overlap_score("blue sky today", "blue")
    assert overlap >= 0.8


def test_keyword_overlap_fail():
    score, passed = score_output("I don't know.", "Paris")
    assert passed is False
    assert score < 0.8
