from typing import Annotated, Any

from langgraph.graph import add_messages
from typing_extensions import TypedDict


class InventoryState(TypedDict):
    messages: Annotated[list, add_messages]
    audit_id: str
    triggered_at: str
    force_approval: bool

    skus: list[str]
    stock_levels: dict[str, int]
    demand_forecasts: dict[str, dict[str, Any]]
    lead_time_days: dict[str, int]

    deficit_skus: list[str]
    rop: dict[str, float]
    eoq: dict[str, float]
    shortfalls: dict[str, int]

    selected_suppliers: dict[str, str]
    supplier_details: dict[str, dict[str, Any]]
    order_proposals: dict[str, dict[str, Any]]

    total_order_value: float
    risk_score: float
    escalation_reason: str | None
    requires_approval: bool
    approved: bool | None

    input_security: dict | None
    iteration: int
    max_iterations: int
    final_message: str | None
