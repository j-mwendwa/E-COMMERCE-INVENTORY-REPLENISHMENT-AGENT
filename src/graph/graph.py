import structlog
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from src.graph.checkpointer import CHECKPOINT_PATH
from src.graph.edges import (
    route_after_escalation,
    route_after_input_check,
    should_continue,
)
from src.graph.guardrails import input_guard_node, output_guard_node
from src.graph.nodes import (
    demand_forecast_node,
    escalation_check_node,
    finalize_node,
    order_generation_node,
    rejection_node,
    stock_monitor_node,
    supplier_selection_node,
)
from src.graph.state import InventoryState

log = structlog.get_logger()
_async_app: CompiledGraph | None = None


def build_graph() -> StateGraph:
    workflow = StateGraph(InventoryState)

    workflow.add_node("input_guardrail", input_guard_node)
    workflow.add_node("rejection_node", rejection_node)
    workflow.add_node("stock_monitor_node", stock_monitor_node)
    workflow.add_node("demand_forecast_node", demand_forecast_node)
    workflow.add_node("supplier_selection_node", supplier_selection_node)
    workflow.add_node("order_generation_node", order_generation_node)
    workflow.add_node("escalation_check_node", escalation_check_node)
    workflow.add_node("finalize_node", finalize_node)
    workflow.add_node("output_guardrail", output_guard_node)

    workflow.set_entry_point("input_guardrail")

    workflow.add_conditional_edges(
        "input_guardrail",
        route_after_input_check,
        {"rejection_node": "rejection_node", "stock_monitor_node": "stock_monitor_node"},
    )

    workflow.add_edge("rejection_node", END)
    workflow.add_edge("stock_monitor_node", "demand_forecast_node")

    workflow.add_conditional_edges(
        "demand_forecast_node",
        should_continue,
        {"supplier_selection_node": "supplier_selection_node", "end": "finalize_node"},
    )

    workflow.add_edge("supplier_selection_node", "order_generation_node")
    workflow.add_edge("order_generation_node", "escalation_check_node")

    workflow.add_conditional_edges(
        "escalation_check_node",
        route_after_escalation,
        {"human_in_the_loop": "finalize_node", "finalize_node": "finalize_node"},
    )

    workflow.add_edge("finalize_node", "output_guardrail")
    workflow.add_edge("output_guardrail", END)

    return workflow


async def get_app_async() -> CompiledGraph:
    global _async_app
    if _async_app is not None:
        return _async_app

    log.info("compiling_graph")
    workflow = build_graph()
    saver = AsyncSqliteSaver.from_conn_string(str(CHECKPOINT_PATH))
    _async_app = workflow.compile(checkpointer=saver)
    log.info("graph_compiled", checkpointer=str(CHECKPOINT_PATH))
    return _async_app


async def reset_app() -> None:
    global _async_app
    _async_app = None
