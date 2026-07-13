import structlog

from src.graph.state import InventoryState

log = structlog.get_logger()


def route_after_input_check(state: InventoryState) -> str:
    decision = state.get("input_security", {}).get("decision", "PASS")
    if decision == "BLOCKED":
        log.info("route.input_guard_blocked", reason=state.get("input_security", {}).get("reason"))
        return "rejection_node"
    return "stock_monitor_node"


def should_continue(state: InventoryState) -> str:
    deficits = state.get("deficit_skus", [])
    if not deficits:
        log.info("route.no_deficits", msg="All stock levels adequate")
        return "end"
    return "supplier_selection_node"


def route_after_escalation(state: InventoryState) -> str:
    if state.get("requires_approval"):
        log.info("route.escalation", msg="Manager approval required")
        return "human_in_the_loop"
    return "finalize_node"


def route_after_approval(state: InventoryState) -> str:
    if state.get("approved") is True or state.get("approved") is None:
        return "finalize_node"
    return "finalize_node"
