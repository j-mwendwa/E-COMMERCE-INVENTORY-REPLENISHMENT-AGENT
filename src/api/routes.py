import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends

from src.api.auth import require_api_key
from src.api.schemas import (
    ApprovalRequest,
    AuditResult,
    AuditTriggerRequest,
    EscalationInfo,
    HealthResponse,
    OrderProposal,
    StockLevel,
    VersionResponse,
)
from src.core.tracing import traceable
from src.graph.checkpointer import run_audit, run_audit_with_approval
from src.graph.state import InventoryState

log = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
@traceable(name="health")
async def health():
    return HealthResponse()


@router.get("/version", response_model=VersionResponse)
@traceable(name="version")
async def version():
    return VersionResponse()


@router.post("/audit", response_model=AuditResult)
@traceable(name="trigger_audit")
async def trigger_audit(
    body: AuditTriggerRequest,
    _api_key: str = Depends(require_api_key),
):
    audit_id = str(uuid.uuid4())
    log.info("audit_triggered", audit_id=audit_id, skus=body.skus)

    config = {"configurable": {"thread_id": audit_id, "force_approval": body.force_approval}}
    result = await run_audit(body.skus, config)

    return _state_to_result(audit_id, result)


@router.post("/audit/{audit_id}/approve", response_model=AuditResult)
@traceable(name="approve_audit")
async def approve_audit(
    audit_id: str,
    body: ApprovalRequest,
    _api_key: str = Depends(require_api_key),
):
    log.info("audit_approval", audit_id=audit_id, approved=body.approved)

    config = {"configurable": {"thread_id": audit_id, "force_approval": False}}
    result = await run_audit_with_approval(audit_id, body.approved, config)

    return _state_to_result(audit_id, result)


@traceable(name="_state_to_result")
def _state_to_result(audit_id: str, state: InventoryState) -> AuditResult:
    stock_levels = []
    for sku in state.get("skus", []):
        current = state.get("stock_levels", {}).get(sku, 0)
        rop = state.get("rop", {}).get(sku, 0)
        deficit = current - rop if current < rop else 0
        shortfall_val = max(0, -int(deficit))
        stock_levels.append(
            StockLevel(sku=sku, current_stock=current, reorder_point=rop, shortfall=shortfall_val)
        )

    proposals = []
    for sku, proposal in state.get("order_proposals", {}).items():
        proposals.append(
            OrderProposal(
                supplier_name=proposal.get("supplier_name", ""),
                sku=sku,
                quantity=proposal.get("quantity", 0),
                total_cost=proposal.get("total_cost", 0.0),
                lead_time_days=proposal.get("lead_time_days", 0),
            )
        )

    escalation = None
    if state.get("requires_approval"):
        escalation = EscalationInfo(
            requires_approval=True,
            total_order_value=state.get("total_order_value", 0.0),
            risk_score=state.get("risk_score", 0.0),
            reason=state.get("escalation_reason"),
        )

    return AuditResult(
        audit_id=audit_id,
        triggered_at=datetime.now(UTC),
        status="completed" if state.get("approved") is not False else "pending_approval",
        stock_levels=stock_levels,
        deficits=state.get("deficit_skus", []),
        order_proposals=proposals,
        escalation=escalation,
        approved=state.get("approved"),
        final_message=state.get("final_message"),
    )
