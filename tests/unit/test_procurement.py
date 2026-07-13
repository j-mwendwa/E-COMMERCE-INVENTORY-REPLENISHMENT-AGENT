from src.models.procurement import PurchaseOrder, Supplier


def test_supplier_unit_price():
    s = Supplier(
        name="TestCo",
        skus=["SKU-A"],
        lead_time_days=5,
        unit_prices={"SKU-A": 10.0},
        min_order_quantities={"SKU-A": 10},
        reliability_score=0.9,
    )
    assert s.unit_price_for("SKU-A") == 10.0
    assert s.unit_price_for("SKU-B") == 0.0


def test_supplier_min_order():
    s = Supplier(
        name="TestCo",
        skus=["SKU-A"],
        lead_time_days=5,
        unit_prices={"SKU-A": 10.0},
        min_order_quantities={"SKU-A": 50},
        reliability_score=0.9,
    )
    assert s.min_order_for("SKU-A") == 50
    assert s.min_order_for("SKU-B") == 0


def test_purchase_order_creation():
    s = Supplier(
        name="TestCo",
        skus=["SKU-A"],
        lead_time_days=5,
        unit_prices={"SKU-A": 10.0},
        min_order_quantities={"SKU-A": 10},
        reliability_score=0.9,
    )
    po = PurchaseOrder.create(s, "SKU-A", 25)
    assert po.supplier_name == "TestCo"
    assert po.quantity == 25
    assert po.unit_price == 10.0
    assert po.total_cost == 250.0
    assert po.lead_time_days == 5
    assert po.status == "draft"


def test_purchase_order_default_status():
    po = PurchaseOrder(
        supplier_name="S",
        sku="SKU-A",
        quantity=10,
        unit_price=5.0,
        total_cost=50.0,
        lead_time_days=3,
    )
    assert po.status == "draft"
