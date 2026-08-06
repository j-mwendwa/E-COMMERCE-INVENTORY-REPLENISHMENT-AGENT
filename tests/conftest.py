"""Shared fixtures for inventory replenishment tests."""

from typing import Any

import pytest


@pytest.fixture
def sample_stock_levels() -> dict[str, int]:
    return {
        "SKU-A100": 25,
        "SKU-B200": 120,
        "SKU-C300": 8,
        "SKU-D400": 60,
        "SKU-E500": 3,
    }


@pytest.fixture
def sample_forecasts() -> dict[str, dict[str, Any]]:
    return {
        "SKU-A100": {
            "avg_daily_demand": 5.0,
            "std_daily_demand": 1.5,
            "trend": 0.1,
            "seasonal_factor": 1.0,
            "promotional_impact": 1.0,
            "confidence": 0.85,
        },
        "SKU-B200": {
            "avg_daily_demand": 12.0,
            "std_daily_demand": 3.0,
            "trend": -0.05,
            "seasonal_factor": 1.0,
            "promotional_impact": 1.0,
            "confidence": 0.9,
        },
        "SKU-C300": {
            "avg_daily_demand": 3.0,
            "std_daily_demand": 1.0,
            "trend": 0.2,
            "seasonal_factor": 1.0,
            "promotional_impact": 1.2,
            "confidence": 0.7,
        },
        "SKU-D400": {
            "avg_daily_demand": 8.0,
            "std_daily_demand": 2.0,
            "trend": 0.0,
            "seasonal_factor": 1.0,
            "promotional_impact": 1.0,
            "confidence": 0.8,
        },
        "SKU-E500": {
            "avg_daily_demand": 2.0,
            "std_daily_demand": 0.5,
            "trend": -0.1,
            "seasonal_factor": 1.0,
            "promotional_impact": 1.0,
            "confidence": 0.95,
        },
    }


@pytest.fixture
def sample_lead_times() -> dict[str, int]:
    return {
        "SKU-A100": 7,
        "SKU-B200": 14,
        "SKU-C300": 7,
        "SKU-D400": 3,
        "SKU-E500": 10,
    }


@pytest.fixture
async def clean_state() -> dict:
    return {
        "messages": [],
        "audit_id": "test-audit",
        "triggered_at": "",
        "force_approval": False,
        "skus": [],
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
