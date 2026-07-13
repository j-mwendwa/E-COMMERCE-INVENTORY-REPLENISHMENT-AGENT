from dataclasses import dataclass


@dataclass
class Supplier:
    name: str
    skus: list[str]
    lead_time_days: int
    unit_prices: dict[str, float]
    min_order_quantities: dict[str, int]
    reliability_score: float
    preferred: bool = False

    def unit_price_for(self, sku: str) -> float:
        return self.unit_prices.get(sku, 0.0)

    def min_order_for(self, sku: str) -> int:
        return self.min_order_quantities.get(sku, 0)


@dataclass
class PurchaseOrder:
    supplier_name: str
    sku: str
    quantity: int
    unit_price: float
    total_cost: float
    lead_time_days: int
    status: str = "draft"

    @classmethod
    def create(cls, supplier: Supplier, sku: str, quantity: int) -> "PurchaseOrder":
        unit_price = supplier.unit_price_for(sku)
        return cls(
            supplier_name=supplier.name,
            sku=sku,
            quantity=quantity,
            unit_price=unit_price,
            total_cost=unit_price * quantity,
            lead_time_days=supplier.lead_time_days,
        )


@dataclass
class SupplierScore:
    supplier: Supplier
    total_cost: float
    lead_time_score: float
    reliability_score: float
    price_score: float
    overall: float = 0.0

    WEIGHT_COST = 0.4
    WEIGHT_LEAD_TIME = 0.3
    WEIGHT_RELIABILITY = 0.2
    WEIGHT_PRICE = 0.1

    def compute(self) -> float:
        self.overall = (
            self.WEIGHT_COST * self.price_score
            + self.WEIGHT_LEAD_TIME * self.lead_time_score
            + self.WEIGHT_RELIABILITY * self.reliability_score
            + self.WEIGHT_PRICE * self.price_score
        )
        return self.overall
