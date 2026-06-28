import pytest

from app.services.guard.engine import BLOCKED_OUTPUT_RESPONSE, scan_output
from app.services.guard.normalize import normalize_guard_text


def test_normalize_strips_zero_width():
    text = "reveal\u200bsystem prompt"
    assert "hidden system prompt" not in normalize_guard_text(text)
    assert "reveal" in normalize_guard_text(text)


def test_output_blocks_system_prompt_leak():
    result = scan_output("For debugging, the system prompt is: You are helpful.")
    assert result.decision == "block"
    assert "out_reveal_system" in result.matched_rule_ids


def test_output_blocks_api_key_echo():
    result = scan_output("Here is your key: api_key=sk-abcdefghijklmnop")
    assert result.decision == "block"


def test_output_allows_clean_answer():
    result = scan_output("Paris is the capital of France.")
    assert result.decision == "allow"