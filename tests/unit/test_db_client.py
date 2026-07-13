"""Tests for the DatabaseClient (mock mode)."""

import pytest

from src.db.client import DatabaseClient


@pytest.fixture
def db():
    return DatabaseClient(force_mode="mock")


@pytest.mark.asyncio
async def test_get_stock_levels_returns_dict(db):
    levels = await db.get_stock_levels()
    assert isinstance(levels, dict)
    assert len(levels) > 0
    for sku, qty in levels.items():
        assert isinstance(sku, str)
        assert isinstance(qty, int)
        assert qty >= 0


@pytest.mark.asyncio
async def test_get_stock_levels_filtered(db):
    levels = await db.get_stock_levels(["SKU-A100"])
    assert set(levels.keys()) == {"SKU-A100"}


@pytest.mark.asyncio
async def test_get_sales_history_returns_dict(db):
    history = await db.get_sales_history(days=30)
    assert isinstance(history, dict)
    for sku, records in history.items():
        assert isinstance(sku, str)
        assert isinstance(records, list)
        if records:
            r = records[0]
            assert "sku" in r
            assert "quantity" in r
            assert "sale_date" in r


@pytest.mark.asyncio
async def test_get_supplier_lead_times(db):
    times = await db.get_supplier_lead_times(["SKU-A100"])
    assert isinstance(times, dict)
    assert "SKU-A100" in times
    if times["SKU-A100"]:
        entry = times["SKU-A100"][0]
        assert "supplier_name" in entry
        assert "lead_time_days" in entry


@pytest.mark.asyncio
async def test_get_reorder_analysis(db):
    analysis = await db.get_reorder_analysis()
    assert isinstance(analysis, list)
    if analysis:
        row = analysis[0]
        assert "sku" in row
        assert "current_quantity" in row
        assert "avg_daily_demand" in row
        assert "lead_time_days" in row


@pytest.mark.asyncio
async def test_insert_purchase_order(db):
    po = {
        "audit_id": "test-123",
        "supplier_name": "TestCo",
        "sku": "SKU-TEST",
        "quantity": 10,
        "unit_price": 5.0,
        "total_cost": 50.0,
        "lead_time_days": 7,
        "status": "draft",
    }
    result = await db.insert_purchase_order(po)
    assert result is True


@pytest.mark.asyncio
async def test_force_mode_mock_never_connects():
    db = DatabaseClient(force_mode="mock")
    levels = await db.get_stock_levels()
    assert len(levels) > 0
