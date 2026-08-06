from src.core.tracing import traceable
from src.models.procurement import Supplier

_MOCK_SUPPLIERS: list[Supplier] = [
    Supplier(
        name="GlobalSupply Co.",
        skus=["SKU-A100", "SKU-B200", "SKU-C300"],
        lead_time_days=7,
        unit_prices={"SKU-A100": 12.50, "SKU-B200": 8.75, "SKU-C300": 22.00},
        min_order_quantities={"SKU-A100": 50, "SKU-B200": 100, "SKU-C300": 25},
        reliability_score=0.92,
        preferred=True,
    ),
    Supplier(
        name="FastShip Logistics",
        skus=["SKU-A100", "SKU-D400", "SKU-E500"],
        lead_time_days=3,
        unit_prices={"SKU-A100": 15.00, "SKU-D400": 45.00, "SKU-E500": 30.00},
        min_order_quantities={"SKU-A100": 20, "SKU-D400": 10, "SKU-E500": 15},
        reliability_score=0.88,
    ),
    Supplier(
        name="Bulk Distributors Inc.",
        skus=["SKU-B200", "SKU-C300", "SKU-D400"],
        lead_time_days=14,
        unit_prices={"SKU-B200": 6.50, "SKU-C300": 18.00, "SKU-D400": 38.00},
        min_order_quantities={"SKU-B200": 500, "SKU-C300": 200, "SKU-D400": 50},
        reliability_score=0.95,
        preferred=True,
    ),
    Supplier(
        name="EconoParts Ltd.",
        skus=["SKU-E500", "SKU-A100"],
        lead_time_days=10,
        unit_prices={"SKU-E500": 25.00, "SKU-A100": 11.00},
        min_order_quantities={"SKU-E500": 30, "SKU-A100": 100},
        reliability_score=0.78,
    ),
]


@traceable(name="search_suppliers_for_sku")
def search_suppliers_for_sku(sku: str) -> list[Supplier]:
    matching = [s for s in _MOCK_SUPPLIERS if sku in s.skus]
    matching.sort(
        key=lambda s: (
            -s.reliability_score,
            s.unit_price_for(sku) if s.unit_price_for(sku) > 0 else float("inf"),
            s.lead_time_days,
        )
    )
    return matching


@traceable(name="get_all_suppliers")
def get_all_suppliers() -> list[Supplier]:
    return list(_MOCK_SUPPLIERS)
