from dataclasses import dataclass
from typing import Literal

from app.services.guard.matcher import find_hits
from app.services.guard.ml_classifier import ML_RULE_ID, ml_decision, predict_unsafe
from app.services.guard.normalize import normalize_guard_text
from app.services.guard.rules import GuardRule, INPUT_RULES, OUTPUT_RULES, RuleScope, rules_for_scope

Decision = Literal["allow", "warn", "block"]

BLOCKED_INPUT_RESPONSE = "Blocked: input failed guard check. LLM not called."
BLOCKED_OUTPUT_RESPONSE = "Blocked: model output matched a safety rule."

_DECISION_RANK = {"allow": 0, "warn": 1, "block": 2}


@dataclass(frozen=True)
class GuardScanResult:
    decision: Decision
    matched_rule_ids: list[str]
    hits: list[GuardRule]
    normalized_text: str
    ml_enabled: bool = False
    ml_loaded: bool = False
    ml_score: float | None = None
    ml_label: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision != "block"

    def hit_payload(self) -> list[dict]:
        return [
            {
                "rule_id": rule.id,
                "name": rule.name,
                "category": rule.category,
                "pattern": rule.pattern,
                "match_type": rule.match_type,
                "severity": rule.severity,
                "scope": rule.scope,
                "description": rule.description,
            }
            for rule in self.hits
        ]


def _classify(hits: list[GuardRule]) -> Decision:
    if not hits:
        return "allow"
    if any(rule.severity == "block" for rule in hits):
        return "block"
    return "warn"


def _merge_decision(current: Decision, incoming: Decision) -> Decision:
    if _DECISION_RANK[incoming] > _DECISION_RANK[current]:
        return incoming
    return current


def _apply_ml(
    scope: RuleScope,
    normalized: str,
    decision: Decision,
    matched_rule_ids: list[str],
) -> tuple[Decision, list[str], bool, bool, float | None, str | None]:
    if scope != "input":
        return decision, matched_rule_ids, False, False, None, None

    ml = predict_unsafe(normalized)
    if not ml.enabled:
        return decision, matched_rule_ids, False, False, None, None

    ml_hit = ml_decision(ml.unsafe_score)
    if ml_hit == "block":
        decision = _merge_decision(decision, "block")
        if ML_RULE_ID not in matched_rule_ids:
            matched_rule_ids = [*matched_rule_ids, ML_RULE_ID]
    elif ml_hit == "warn":
        decision = _merge_decision(decision, "warn")

    return decision, matched_rule_ids, ml.enabled, ml.loaded, ml.unsafe_score, ml.label


def scan_text(text: str, scope: RuleScope) -> GuardScanResult:
    normalized = normalize_guard_text(text)
    hits = find_hits(normalized, rules_for_scope(scope))
    decision = _classify(hits)
    block_ids = [rule.id for rule in hits if rule.severity == "block"]
    matched_rule_ids = block_ids or [rule.id for rule in hits]

    decision, matched_rule_ids, ml_enabled, ml_loaded, ml_score, ml_label = _apply_ml(
        scope, normalized, decision, matched_rule_ids
    )

    return GuardScanResult(
        decision=decision,
        matched_rule_ids=matched_rule_ids,
        hits=hits,
        normalized_text=normalized,
        ml_enabled=ml_enabled,
        ml_loaded=ml_loaded,
        ml_score=ml_score,
        ml_label=ml_label,
    )


def scan_input(text: str) -> tuple[bool, list[str]]:
    result = scan_text(text, "input")
    if result.decision == "block":
        return False, result.matched_rule_ids
    return True, result.matched_rule_ids


def scan_output(text: str) -> GuardScanResult:
    return scan_text(text, "output")


def _result_payload(result: GuardScanResult) -> dict:
    return {
        "allowed": result.decision != "block",
        "decision": result.decision,
        "matched_rule_ids": result.matched_rule_ids,
        "hits": result.hit_payload(),
        "ml_enabled": result.ml_enabled,
        "ml_loaded": result.ml_loaded,
        "ml_score": result.ml_score,
        "ml_label": result.ml_label,
    }


def scan_input_detailed(text: str) -> dict:
    return _result_payload(scan_text(text, "input"))


def scan_output_detailed(text: str) -> dict:
    return _result_payload(scan_text(text, "output"))


def list_rules(scope: RuleScope | None = None) -> list[GuardRule]:
    if scope:
        return rules_for_scope(scope)
    return list(INPUT_RULES) + list(OUTPUT_RULES)