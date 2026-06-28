from fastapi import APIRouter, HTTPException

from app.models import GuardRuleInfo, GuardRulesResponse, GuardScanRequest, GuardScanResponse
from app.services.guard.engine import list_rules, scan_input_detailed, scan_output_detailed

router = APIRouter()


@router.get("/guard/rules", response_model=GuardRulesResponse)
async def get_guard_rules(scope: str | None = None):
    if scope and scope not in {"input", "output"}:
        raise HTTPException(status_code=400, detail="scope must be 'input' or 'output'")
    rules = list_rules(scope)  # type: ignore[arg-type]
    return GuardRulesResponse(
        count=len(rules),
        rules=[
            GuardRuleInfo(
                id=rule.id,
                name=rule.name,
                category=rule.category,
                pattern=rule.pattern,
                match_type=rule.match_type,
                severity=rule.severity,
                scope=rule.scope,
                description=rule.description,
            )
            for rule in rules
        ],
    )


@router.post("/guard/scan", response_model=GuardScanResponse)
async def scan_guard_text(payload: GuardScanRequest):
    if payload.scope == "output":
        result = scan_output_detailed(payload.text)
    else:
        result = scan_input_detailed(payload.text)
    return GuardScanResponse(**result)