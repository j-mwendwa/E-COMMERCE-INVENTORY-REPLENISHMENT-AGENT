from src.models.demand import DemandForecast, LeadTime


def test_demand_forecast_adjustment():
    f = DemandForecast(
        sku="SKU-TEST",
        avg_daily_demand=10.0,
        std_daily_demand=2.0,
        trend=0.0,
        seasonal_factor=1.2,
        promotional_impact=1.5,
    )
    assert f.adjusted_daily_demand == 10.0 * 1.2 * 1.5


def test_demand_forecast_annual():
    f = DemandForecast(
        sku="SKU-TEST",
        avg_daily_demand=10.0,
        std_daily_demand=2.0,
        trend=0.0,
    )
    assert f.annual_demand == 10.0 * 365


def test_lead_time_reliability():
    lt = LeadTime(
        supplier_name="TestCo",
        sku="SKU-A",
        min_days=3,
        max_days=7,
        avg_days=5,
        reliability=0.95,
    )
    assert lt.is_reliable() is True
    assert lt.is_reliable(0.96) is False
