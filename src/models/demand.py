from dataclasses import dataclass


@dataclass
class DemandForecast:
    sku: str
    avg_daily_demand: float
    std_daily_demand: float
    trend: float
    seasonal_factor: float = 1.0
    promotional_impact: float = 1.0
    confidence: float = 0.8

    @property
    def adjusted_daily_demand(self) -> float:
        return self.avg_daily_demand * self.seasonal_factor * self.promotional_impact

    @property
    def annual_demand(self) -> float:
        return self.adjusted_daily_demand * 365


@dataclass
class LeadTime:
    supplier_name: str
    sku: str
    min_days: int
    max_days: int
    avg_days: int
    reliability: float = 0.95

    def is_reliable(self, threshold: float = 0.9) -> bool:
        return self.reliability >= threshold
