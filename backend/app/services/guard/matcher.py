import re

from app.services.guard.rules import GuardRule, MatchType


def rule_matches(text: str, rule: GuardRule) -> bool:
    if rule.match_type == "phrase":
        return rule.pattern.lower() in text.lower()
    return re.search(rule.pattern, text, flags=re.IGNORECASE) is not None


def find_hits(text: str, rules: list[GuardRule]) -> list[GuardRule]:
    return [rule for rule in rules if rule_matches(text, rule)]