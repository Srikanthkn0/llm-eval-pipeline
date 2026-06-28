from dataclasses import dataclass
from typing import Literal

MatchType = Literal["phrase", "regex"]
RuleScope = Literal["input", "output"]
Severity = Literal["block", "warn"]


@dataclass(frozen=True)
class GuardRule:
    id: str
    name: str
    category: str
    pattern: str
    scope: RuleScope
    severity: Severity = "block"
    match_type: MatchType = "phrase"
    description: str = ""


INPUT_RULES: list[GuardRule] = [
    GuardRule("inj_ignore_prev", "Ignore previous instructions", "prompt_injection", "ignore previous instructions", "input", description="Override prior instructions."),
    GuardRule("inj_reveal_system", "Reveal system prompt", "prompt_injection", "reveal system prompt", "input", description="Extract system instructions."),
    GuardRule("inj_show_hidden", "Show hidden prompt", "prompt_injection", "show hidden prompt", "input", description="Expose hidden prompt."),
    GuardRule("inj_hidden_system", "Hidden system prompt", "prompt_injection", "hidden system prompt", "input", description="Reference hidden system text."),
    GuardRule("inj_internal_config", "Internal configuration", "prompt_injection", "internal configuration", "input", description="Request internal config."),
    GuardRule("inj_disregard", "Disregard instructions", "prompt_injection", "disregard your instructions", "input", description="Discard standing instructions."),
    GuardRule("inj_disregard_short", "Disregard all", "prompt_injection", "disregard all", "input", description="Broad instruction discard."),
    GuardRule("inj_forget_rules", "Forget rules", "prompt_injection", "forget your rules", "input", description="Drop policy constraints."),
    GuardRule("inj_what_instructions", "What were instructions", "prompt_injection", "what were your instructions", "input", description="Probe for system message."),
    GuardRule("inj_repeat_system", "Repeat system", "prompt_injection", "repeat the system", "input", description="Verbatim system extraction."),
    GuardRule("inj_print_system", "Print system prompt", "prompt_injection", "print system prompt", "input", description="Dump system prompt."),
    GuardRule("inj_dump_prompt", "Dump prompt", "prompt_injection", "dump your prompt", "input", description="Full prompt dump."),
    GuardRule("inj_above_instructions", "Ignore above", "prompt_injection", "ignore the above", "input", description="Override earlier context."),
    GuardRule("inj_new_instructions", "New instructions", "prompt_injection", "your new instructions are", "input", description="Inject replacement instructions."),
    GuardRule("inj_reveal_fuzzy", "Reveal fuzzy", "prompt_injection", r"reveal.{0,80}(system prompt|hidden prompt|internal configuration|instructions)", "input", match_type="regex", description="Flexible reveal phrasing."),
    GuardRule("inj_ignore_fuzzy", "Ignore fuzzy", "prompt_injection", r"ignore.{0,40}(previous|above|prior|all).{0,40}(instructions|rules|prompt)", "input", match_type="regex", description="Flexible ignore phrasing."),
    GuardRule("inj_override_fuzzy", "Override fuzzy", "prompt_injection", r"(disregard|forget|override).{0,40}((system|safety|content).{0,20})?(rules|instructions|policy)", "input", match_type="regex", description="Policy override variants."),
    GuardRule("inj_bypass_safety", "Bypass safety", "jailbreak", "bypass safety", "input", description="Disable safety."),
    GuardRule("inj_dev_mode", "Developer mode", "jailbreak", "act as developer mode", "input", description="Developer-mode jailbreak."),
    GuardRule("inj_dev_mode_short", "Enter developer mode", "jailbreak", "enter developer mode", "input", description="Developer-mode variant."),
    GuardRule("inj_dan", "DAN", "jailbreak", "do anything now", "input", description="DAN jailbreak."),
    GuardRule("inj_dan_acronym", "You are DAN", "jailbreak", "you are dan", "input", description="DAN persona."),
    GuardRule("inj_unrestricted", "Unrestricted AI", "jailbreak", "unrestricted ai", "input", description="Unrestricted mode."),
    GuardRule("inj_no_restrictions", "No restrictions", "jailbreak", "no restrictions", "input", description="No limits framing."),
    GuardRule("inj_pretend", "Pretend persona", "jailbreak", "pretend you are", "input", severity="warn", description="Persona swap."),
    GuardRule("inj_roleplay_evil", "Evil roleplay", "jailbreak", "pretend you have no ethical", "input", description="Ethics removal."),
    GuardRule("inj_opposite", "Opposite mode", "jailbreak", "opposite mode", "input", description="Opposite-day jailbreak."),
    GuardRule("inj_sudo", "Sudo mode", "jailbreak", "sudo mode", "input", description="Elevated mode framing."),
    GuardRule("inj_jailbreak_word", "Jailbreak", "jailbreak", "jailbreak", "input", description="Explicit jailbreak."),
    GuardRule("inj_simulation", "Simulation mode", "jailbreak", "simulation mode", "input", description="Simulation bypass."),
    GuardRule("inj_override_rules", "Override rules", "policy_bypass", "override rules", "input", severity="warn", description="Rule override."),
    GuardRule("inj_without_filters", "Without filters", "policy_bypass", "without filters", "input", severity="warn", description="Unfiltered output request."),
    GuardRule("inj_disable_safety", "Disable safety", "policy_bypass", "disable safety", "input", description="Turn off safety."),
    GuardRule("inj_ignore_guidelines", "Ignore guidelines", "policy_bypass", "ignore your guidelines", "input", description="Discard guidelines."),
    GuardRule("inj_print_secrets", "Print secrets", "credential_request", "print secrets", "input", description="Expose secrets."),
    GuardRule("inj_show_api_key", "Show API key", "credential_request", "show api key", "input", description="API key disclosure."),
    GuardRule("inj_cred_api_key", "API key assignment", "credential_request", r"(?i)\bapi[_ -]?key\s*[:=]\s*\S+", "input", match_type="regex", description="Key in prompt."),
    GuardRule("inj_cred_token", "Token assignment", "credential_request", r"(?i)\b(password|secret|token)\s*[:=]\s*\S+", "input", match_type="regex", description="Credential in prompt."),
    GuardRule("inj_cred_sk", "Stripe-style key", "credential_request", r"sk-[A-Za-z0-9]{10,}", "input", match_type="regex", description="Secret key marker."),
    GuardRule("inj_training_data", "Training data", "data_extraction", "reveal your training data", "input", description="Training data extract."),
    GuardRule("inj_repeat_verbatim", "Repeat verbatim", "data_extraction", "repeat everything above verbatim", "input", description="Context extraction."),
]

OUTPUT_RULES: list[GuardRule] = [
    GuardRule("out_reveal_system", "System prompt leak", "data_leak", "system prompt is", "output", description="Output exposes system prompt."),
    GuardRule("out_hidden_instructions", "Hidden instructions leak", "data_leak", "hidden instructions are", "output", description="Output exposes hidden instructions."),
    GuardRule("out_internal_config", "Internal config leak", "data_leak", "internal configuration", "output", severity="warn", description="Output mentions internal config."),
    GuardRule("out_api_key", "API key in output", "credential_leak", r"(?i)\bapi[_ -]?key\s*[:=]\s*\S+", "output", match_type="regex", description="API key in model output."),
    GuardRule("out_token_like", "Token in output", "credential_leak", r"(?i)\b(password|secret|token)\s*[:=]\s*\S+", "output", match_type="regex", description="Credential in output."),
    GuardRule("out_sk_live", "Stripe key in output", "credential_leak", r"sk-[A-Za-z0-9]{10,}", "output", match_type="regex", description="Secret key in output."),
    GuardRule("out_destructive_cmd", "Destructive command", "unsafe_content", r"(?i)\brm\s+-rf\b", "output", severity="warn", description="Destructive shell command."),
    GuardRule("out_disable_safety", "Disable safety in output", "policy_bypass", "disable safety", "output", severity="warn", description="Output encourages disabling safety."),
]

ALL_RULES: list[GuardRule] = INPUT_RULES + OUTPUT_RULES


def rules_for_scope(scope: RuleScope) -> list[GuardRule]:
    return [rule for rule in ALL_RULES if rule.scope == scope]