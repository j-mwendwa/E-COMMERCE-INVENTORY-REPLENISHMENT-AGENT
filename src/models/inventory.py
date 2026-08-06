import math
from dataclasses import dataclass


@dataclass
class StockLevel:
    sku: str
    current_quantity: int
    reserved_quantity: int = 0

    @property
    def available(self) -> int:
        return self.current_quantity - self.reserved_quantity


@dataclass
class ReorderPoint:
    sku: str
    avg_daily_demand: float
    lead_time_days: int
    safety_stock_multiplier: float = 1.5

    @property
    def value(self) -> float:
        return self.avg_daily_demand * self.lead_time_days * self.safety_stock_multiplier

    @property
    def safety_stock(self) -> float:
        return self.avg_daily_demand * self.lead_time_days * (self.safety_stock_multiplier - 1)


@dataclass
class EconomicOrderQuantity:
    sku: str
    annual_demand: float
    order_cost: float = 50.0
    holding_cost_rate: float = 0.25
    unit_cost: float = 0.0

    @property
    def value(self) -> float:
        if self.holding_cost_rate * self.unit_cost <= 0:
            return 0.0
        return math.sqrt(
            (2 * self.annual_demand * self.order_cost) / (self.holding_cost_rate * self.unit_cost)
        )


def is_below_reorder_point(current_stock: int, reorder_point: float) -> bool:
    return current_stock < reorder_point


def compute_shortfall(current_stock: int, reorder_point: float) -> int:
    if current_stock >= reorder_point:
        return 0
    return int(math.ceil(reorder_point - current_stock))
