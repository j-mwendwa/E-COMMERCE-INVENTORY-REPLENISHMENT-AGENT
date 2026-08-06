import structlog

log = structlog.get_logger()


async def fetch_stock_levels(skus: list[str] | None = None) -> dict[str, int]:
    import random

    products = skus or [
        "SKU-A100",
        "SKU-B200",
        "SKU-C300",
        "SKU-D400",
        "SKU-E500",
    ]
    levels = {sku: random.randint(0, 100) for sku in products}
    log.info("stock_fetched", skus=list(levels.keys()), total_items=len(levels))
    return levels


async def place_order(supplier: str, sku: str, quantity: int) -> dict:
    log.info("order_placed", supplier=supplier, sku=sku, quantity=quantity)
    return {
        "status": "confirmed",
        "supplier": supplier,
        "sku": sku,
        "quantity": quantity,
        "order_id": f"PO-{supplier[:3].upper()}-{sku}-{hash((supplier, sku, quantity)) % 10000:04d}",  # noqa: E501
    }
