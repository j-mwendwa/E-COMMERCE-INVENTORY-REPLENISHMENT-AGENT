import structlog

from src.config import ROOT_DIR
from src.graph.graph import get_app_async
from src.graph.state import InventoryState

log = structlog.get_logger()

CHECKPOINT_DIR = ROOT_DIR / "data" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = CHECKPOINT_DIR / "checkpoints.db"


async def run_audit(
    skus: list[str] | None = None,
    config: dict | None = None,
) -> InventoryState:
    app = await get_app_async()
    config = config or {"configurable": {"thread_id": "default"}}

    initial_state: InventoryState = {
        "messages": [],
        "audit_id": config["configurable"].get("thread_id", "unknown"),
        "triggered_at": "",
        "force_approval": config["configurable"].get("force_approval", False),
        "skus": skus or [],
        "stock_levels": {},
        "demand_forecasts": {},
        "lead_time_days": {},
        "deficit_skus": [],
        "rop": {},
        "eoq": {},
        "shortfalls": {},
        "selected_suppliers": {},
        "supplier_details": {},
        "order_proposals": {},
        "total_order_value": 0.0,
        "risk_score": 0.0,
        "escalation_reason": None,
        "requires_approval": False,
        "approved": None,
        "input_security": None,
        "iteration": 0,
        "max_iterations": 10,
        "final_message": None,
    }

    result = await app.ainvoke(initial_state, config)
    log.info("audit_completed", final_message=str(result.get("final_message", ""))[:100])
    return result


async def run_audit_with_approval(
    thread_id: str,
    approved: bool,
    config: dict | None = None,
) -> InventoryState:
    app = await get_app_async()
    config = config or {"configurable": {"thread_id": thread_id}}

    state = await app.aget_state(config)
    if not state or not state.values:
        msg = f"No audit found for thread_id: {thread_id}"
        raise ValueError(msg)

    updated = {**state.values, "approved": approved}
    result = await app.ainvoke(updated, config)
    log.info("audit_approval_processed", thread_id=thread_id, approved=approved)
    return result
