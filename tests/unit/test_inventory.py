from src.models.inventory import (
    EconomicOrderQuantity,
    ReorderPoint,
    compute_shortfall,
    is_below_reorder_point,
)


def test_reorder_point_value():
    rop = ReorderPoint(
        sku="SKU-TEST",
        avg_daily_demand=10.0,
        lead_time_days=7,
        safety_stock_multiplier=1.5,
    )
    expected = 10.0 * 7 * 1.5
    assert rop.value == expected


def test_reorder_point_safety_stock():
    rop = ReorderPoint(
        sku="SKU-TEST",
        avg_daily_demand=10.0,
        lead_time_days=7,
        safety_stock_multiplier=1.5,
    )
    assert rop.safety_stock == 10.0 * 7 * 0.5


def test_eoq_value():
    eoq = EconomicOrderQuantity(
        sku="SKU-TEST",
        annual_demand=3650,
        order_cost=50.0,
        holding_cost_rate=0.25,
        unit_cost=10.0,
    )
    expected = ((2 * 3650 * 50.0) / (0.25 * 10.0)) ** 0.5
    assert abs(eoq.value - expected) < 0.01


def test_eoq_zero_when_no_unit_cost():
    eoq = EconomicOrderQuantity(
        sku="SKU-TEST",
        annual_demand=3650,
        order_cost=50.0,
        holding_cost_rate=0.25,
        unit_cost=0.0,
    )
    assert eoq.value == 0.0


def test_is_below_reorder_point():
    assert is_below_reorder_point(10, 15.0) is True
    assert is_below_reorder_point(15, 15.0) is False
    assert is_below_reorder_point(20, 15.0) is False


def test_compute_shortfall():
    assert compute_shortfall(10, 15.0) == 5
    assert compute_shortfall(15, 15.0) == 0
    assert compute_shortfall(20, 15.0) == 0
    assert compute_shortfall(0, 10.0) == 10
