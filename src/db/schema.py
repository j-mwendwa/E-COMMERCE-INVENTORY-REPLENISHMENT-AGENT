"""PostgreSQL schema for the inventory replenishment system."""

SCHEMA_SQL = """
-- Products / SKUs
CREATE TABLE IF NOT EXISTS products (
    sku          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    unit_cost    DECIMAL(10,2) NOT NULL,
    category     TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Current stock levels
CREATE TABLE IF NOT EXISTS stock_levels (
    sku                TEXT PRIMARY KEY REFERENCES products(sku),
    current_quantity   INTEGER NOT NULL DEFAULT 0,
    reserved_quantity  INTEGER NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Sales history for demand forecasting
CREATE TABLE IF NOT EXISTS sales_history (
    id           SERIAL PRIMARY KEY,
    sku          TEXT NOT NULL REFERENCES products(sku),
    sale_date    DATE NOT NULL,
    quantity     INTEGER NOT NULL,
    unit_price   DECIMAL(10,2) NOT NULL
);

-- Supplier lead times
CREATE TABLE IF NOT EXISTS supplier_lead_times (
    supplier_name  TEXT NOT NULL,
    sku            TEXT NOT NULL REFERENCES products(sku),
    lead_time_days INTEGER NOT NULL,
    reliability    DECIMAL(3,2) NOT NULL DEFAULT 0.95,
    PRIMARY KEY (supplier_name, sku)
);

-- Purchase orders (output table)
CREATE TABLE IF NOT EXISTS purchase_orders (
    id              SERIAL PRIMARY KEY,
    audit_id        TEXT NOT NULL,
    supplier_name   TEXT NOT NULL,
    sku             TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    total_cost      DECIMAL(12,2) NOT NULL,
    lead_time_days  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'draft',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    approved_at     TIMESTAMPTZ,
    approved_by     TEXT
);

CREATE INDEX IF NOT EXISTS idx_sales_history_sku ON sales_history(sku);
CREATE INDEX IF NOT EXISTS idx_sales_history_date ON sales_history(sale_date);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_audit ON purchase_orders(audit_id);
"""

SEED_SQL = """
INSERT INTO products (sku, name, unit_cost, category) VALUES
    ('SKU-A100', 'Widget Alpha', 12.50, 'Widgets'),
    ('SKU-B200', 'Gadget Beta', 8.75, 'Gadgets'),
    ('SKU-C300', 'Component Gamma', 22.00, 'Components'),
    ('SKU-D400', 'Device Delta', 45.00, 'Devices'),
    ('SKU-E500', 'Assembly Epsilon', 30.00, 'Assemblies')
ON CONFLICT (sku) DO NOTHING;

INSERT INTO stock_levels (sku, current_quantity, reserved_quantity) VALUES
    ('SKU-A100', 25, 5),
    ('SKU-B200', 120, 10),
    ('SKU-C300', 8, 2),
    ('SKU-D400', 60, 8),
    ('SKU-E500', 3, 1)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO supplier_lead_times (supplier_name, sku, lead_time_days, reliability) VALUES
    ('GlobalSupply Co.', 'SKU-A100', 7, 0.92),
    ('GlobalSupply Co.', 'SKU-B200', 7, 0.92),
    ('GlobalSupply Co.', 'SKU-C300', 7, 0.92),
    ('FastShip Logistics', 'SKU-A100', 3, 0.88),
    ('FastShip Logistics', 'SKU-D400', 3, 0.88),
    ('FastShip Logistics', 'SKU-E500', 3, 0.88),
    ('Bulk Distributors Inc.', 'SKU-B200', 14, 0.95),
    ('Bulk Distributors Inc.', 'SKU-C300', 14, 0.95),
    ('Bulk Distributors Inc.', 'SKU-D400', 14, 0.95),
    ('EconoParts Ltd.', 'SKU-E500', 10, 0.78),
    ('EconoParts Ltd.', 'SKU-A100', 10, 0.78)
ON CONFLICT (supplier_name, sku) DO NOTHING;

INSERT INTO sales_history (sku, sale_date, quantity, unit_price)
SELECT
    sku,
    d::DATE,
    (random() * 20 + 1)::INTEGER,
    unit_cost * (1 + (random() * 0.3))
FROM products
CROSS JOIN LATERAL (
    SELECT generate_series(
        CURRENT_DATE - INTERVAL '90 days',
        CURRENT_DATE,
        '1 day'::INTERVAL
    ) AS d
) AS dates
WHERE random() > 0.3
ON CONFLICT DO NOTHING;
"""

STOCK_QUERY = """
SELECT sku, current_quantity, reserved_quantity, updated_at
FROM stock_levels
ORDER BY sku
"""

SALES_HISTORY_QUERY = """
SELECT sku, sale_date, quantity, unit_price
FROM sales_history
WHERE sku = ANY(%(skus)s)
  AND sale_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY sku, sale_date
"""

LEAD_TIME_QUERY = """
SELECT supplier_name, sku, lead_time_days, reliability
FROM supplier_lead_times
WHERE sku = ANY(%(skus)s)
"""

REORDER_CHECK_QUERY = """
SELECT
    s.sku,
    s.current_quantity,
    COALESCE(AVG(sh.quantity), 0) AS avg_daily_demand,
    COALESCE(MIN(slt.lead_time_days), 14) AS lead_time_days
FROM stock_levels s
LEFT JOIN sales_history sh ON sh.sku = s.sku
    AND sh.sale_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN supplier_lead_times slt ON slt.sku = s.sku
GROUP BY s.sku, s.current_quantity
"""
