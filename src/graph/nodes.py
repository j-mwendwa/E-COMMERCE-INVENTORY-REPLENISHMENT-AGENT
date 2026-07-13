import structlog

from src.config import cfg
from src.core.context_assembler import ContextAssembler
from src.db.client import get_db_client
from src.graph.state import InventoryState
from src.models.inventory import (
    EconomicOrderQuantity,
    ReorderPoint,
    compute_shortfall,
    is_below_reorder_point,
)
from src.tools.supplier_search import search_suppliers_for_sku

log = structlog.get_logger()
context_assembler = ContextAssembler(
    target_tokens=cfg.get("context", {}).get("target_context_tokens", 8000)
)

_db = get_db_client()


async def stock_monitor_node(state: InventoryState) -> dict:
    log.info("node.stock_monitor", skus=state.get("skus"))
    stock_levels = await _db.get_stock_levels(state.get("skus"))
    skus = list(stock_levels.keys())
    log.info("stock_levels_fetched", count=len(skus), source="db" if not _db.is_mock else "mock")
    return {"stock_levels": stock_levels, "skus": skus}


async def demand_forecast_node(state: InventoryState) -> dict:
    log.info("node.demand_forecast")
    stock_levels = state["stock_levels"]
    skus = list(stock_levels.keys())

    reorder_analysis = await _db.get_reorder_analysis()
    analysis_by_sku = {r["sku"]: r for r in reorder_analysis}

    lead_times_data = await _db.get_supplier_lead_times(skus)

    rop: dict[str, float] = {}
    eoq: dict[str, float] = {}
    forecasts: dict[str, dict] = {}
    lead_times_out: dict[str, int] = {}
    deficits: list[str] = []
    shortfalls: dict[str, int] = {}

    for sku in skus:
        analysis = analysis_by_sku.get(sku, {})
        avg_daily = float(analysis.get("avg_daily_demand", 5.0))
        lead_days = int(analysis.get("lead_time_days", 14))

        lead_times_out[sku] = lead_days

        supplier_entries = lead_times_data.get(sku, [])
        best_lead = min((e["lead_time_days"] for e in supplier_entries), default=lead_days)

        forecast = {
            "avg_daily_demand": round(avg_daily, 2),
            "std_daily_demand": round(avg_daily * 0.3, 2),
            "trend": 0.0,
            "seasonal_factor": 1.0,
            "promotional_impact": 1.0,
            "confidence": 0.85,
        }
        forecasts[sku] = forecast

        reorder = ReorderPoint(
            sku=sku,
            avg_daily_demand=avg_daily,
            lead_time_days=best_lead,
            safety_stock_multiplier=cfg.get("inventory", {}).get("safety_stock_multiplier", 1.5),
        )
        rop[sku] = reorder.value

        unit_cost = 12.50
        eoq_calc = EconomicOrderQuantity(
            sku=sku,
            annual_demand=avg_daily * 365,
            order_cost=cfg.get("inventory", {}).get("eoq_order_cost", 50.0),
            holding_cost_rate=cfg.get("inventory", {}).get("eoq_holding_cost_rate", 0.25),
            unit_cost=unit_cost,
        )
        eoq[sku] = eoq_calc.value

        current = stock_levels[sku]
        if is_below_reorder_point(current, rop[sku]):
            deficits.append(sku)
            shortfalls[sku] = compute_shortfall(current, rop[sku])

    log.info(
        "demand_forecast_complete",
        total_skus=len(skus),
        deficits=len(deficits),
        source="db" if not _db.is_mock else "mock",
    )
    return {
        "demand_forecasts": forecasts,
        "lead_time_days": lead_times_out,
        "rop": rop,
        "eoq": eoq,
        "deficit_skus": deficits,
        "shortfalls": shortfalls,
    }


async def supplier_selection_node(state: InventoryState) -> dict:
    log.info("node.supplier_selection", deficit_skus=state.get("deficit_skus", []))
    selected_suppliers: dict[str, str] = {}
    supplier_details: dict[str, dict] = {}

    for sku in state.get("deficit_skus", []):
        suppliers = search_suppliers_for_sku(sku)
        if not suppliers:
            log.warning("no_supplier_found", sku=sku)
            continue

        best = suppliers[0]
        selected_suppliers[sku] = best.name
        supplier_details[sku] = {
            "name": best.name,
            "lead_time_days": best.lead_time_days,
            "unit_price": best.unit_price_for(sku),
            "min_order": best.min_order_for(sku),
            "reliability": best.reliability_score,
        }

    return {"selected_suppliers": selected_suppliers, "supplier_details": supplier_details}


async def order_generation_node(state: InventoryState) -> dict:
    log.info("node.order_generation")
    order_proposals: dict[str, dict] = {}
    total_value = 0.0
    max_risk = 0.0
    risk_reasons: list[str] = []

    for sku in state.get("deficit_skus", []):
        supplier_info = state.get("supplier_details", {}).get(sku)
        if not supplier_info:
            continue

        shortfall = state.get("shortfalls", {}).get(sku, 0)
        moq = supplier_info.get("min_order", 0)
        quantity = max(shortfall, moq)

        if state.get("eoq", {}).get(sku, 0) > 0:
            quantity = max(quantity, int(state["eoq"][sku]))

        total_cost = quantity * supplier_info["unit_price"]
        po = {
            "supplier_name": supplier_info["name"],
            "sku": sku,
            "quantity": quantity,
            "unit_price": supplier_info["unit_price"],
            "total_cost": round(total_cost, 2),
            "lead_time_days": supplier_info["lead_time_days"],
            "status": "draft",
        }
        order_proposals[sku] = po
        total_value += total_cost

        if supplier_info["reliability"] < 0.8:
            max_risk = max(max_risk, 0.7)
            risk_reasons.append(f"Low supplier reliability for {sku}")
        if supplier_info["lead_time_days"] > 14:
            max_risk = max(max_risk, 0.6)
            risk_reasons.append(f"Long lead time for {sku}")

        await _db.insert_purchase_order(po)

    escalation_reason = "; ".join(risk_reasons) if risk_reasons else None
    return {
        "order_proposals": order_proposals,
        "total_order_value": round(total_value, 2),
        "risk_score": round(max(max_risk, 0.1), 2),
        "escalation_reason": escalation_reason,
    }


async def escalation_check_node(state: InventoryState) -> dict:
    threshold = cfg.get("escalation", {}).get("order_value_threshold", 10000.0)
    risk_threshold = cfg.get("escalation", {}).get("risk_score_threshold", 0.7)

    total = state.get("total_order_value", 0.0)
    risk = state.get("risk_score", 0.0)
    force = state.get("force_approval", False)

    requires = force or total > threshold or risk > risk_threshold
    if requires:
        log.info(
            "escalation_required",
            total_order_value=total,
            risk_score=risk,
            threshold=threshold,
            risk_threshold=risk_threshold,
        )

    return {"requires_approval": requires}


async def finalize_node(state: InventoryState) -> dict:
    if state.get("approved") is False:
        return {"final_message": "Purchase orders rejected by manager. No orders placed."}

    if not state.get("requires_approval") or state.get("approved") is True:
        proposals = state.get("order_proposals", {})
        if not proposals:
            return {"final_message": "Audit complete. All stock levels are adequate."}

        lines = []
        for _sku, po in proposals.items():
            lines.append(
                f"- {po.get('sku')}: {po.get('quantity')} units @ ${po.get('unit_price', 0):.2f} "
                f"from {po.get('supplier_name')} (${po.get('total_cost', 0):.2f})"
            )
        total = state.get("total_order_value", 0.0)
        return {
            "final_message": (
                f"Purchase orders generated ({len(proposals)} items, total ${total:.2f}):\n"
                + "\n".join(lines)
            )
        }

    return {"final_message": "Audit requires manager approval."}


async def rejection_node(state: InventoryState) -> dict:
    input_security = state.get("input_security") or {}
    reason = input_security.get("reason", "Input validation failed")
    log.warning("rejection_node", reason=reason)
    return {"final_message": f"Audit rejected: {reason}"}
