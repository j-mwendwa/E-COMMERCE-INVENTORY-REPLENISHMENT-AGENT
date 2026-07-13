"""
DatabaseClient — queries the inventory database directly via psycopg2.

Fallback chain: DATABASE_URL set → direct psycopg2 → mock dummy data
"""

import random

import structlog

from src.config import settings

log = structlog.get_logger()


class DatabaseClient:
    def __init__(self, force_mode: str | None = None) -> None:
        self._mode = force_mode or ("direct" if settings.database_url else "mock")
        log.info("db_mode", mode=self._mode)

    def set_mode(self, mode: str) -> None:
        self._mode = mode

    @property
    def is_mock(self) -> bool:
        return self._mode == "mock"

    async def get_stock_levels(self, skus: list[str] | None = None) -> dict[str, int]:
        if self._mode == "direct":
            return await self._direct_stock_levels(skus)
        return self._mock_stock_levels(skus)

    async def get_sales_history(
        self, skus: list[str] | None = None, days: int = 90,
    ) -> dict[str, list[dict]]:
        if self._mode == "direct":
            return await self._direct_sales_history(skus, days)
        return self._mock_sales_history(skus, days)

    async def get_supplier_lead_times(
        self, skus: list[str] | None = None,
    ) -> dict[str, list[dict]]:
        if self._mode == "direct":
            return await self._direct_supplier_lead_times(skus)
        return self._mock_supplier_lead_times(skus)

    async def get_reorder_analysis(self) -> list[dict]:
        if self._mode == "direct":
            return await self._direct_reorder_analysis()
        return self._mock_reorder_analysis()

    async def insert_purchase_order(self, po: dict) -> bool:
        if self._mode == "direct":
            return await self._direct_insert_po(po)
        log.info("db_mock_insert_po", po=po)
        return True

    # ── direct psycopg2 ──────────────────────────────────

    def _conn(self):
        import psycopg2
        return psycopg2.connect(settings.database_url)

    async def _direct_stock_levels(self, skus: list[str] | None) -> dict[str, int]:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                if skus:
                    cur.execute(
                        "SELECT sku, current_quantity FROM stock_levels WHERE sku = ANY(%s)",
                        (skus,),
                    )
                else:
                    cur.execute("SELECT sku, current_quantity FROM stock_levels")
                return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()

    async def _direct_sales_history(
        self, skus: list[str] | None, days: int,
    ) -> dict[str, list[dict]]:
        import psycopg2.extras
        conn = self._conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT sku, sale_date::TEXT, quantity, unit_price "
                    "FROM sales_history "
                    "WHERE (sku = ANY(%s) OR %s IS NULL) "
                    "AND sale_date >= CURRENT_DATE - %s::INTERVAL "
                    "ORDER BY sku, sale_date",
                    (skus or [], skus, f"{days} days"),
                )
                result: dict[str, list[dict]] = {}
                for row in cur.fetchall():
                    result.setdefault(row["sku"], []).append(dict(row))
                return result
        finally:
            conn.close()

    async def _direct_supplier_lead_times(
        self, skus: list[str] | None,
    ) -> dict[str, list[dict]]:
        import psycopg2.extras
        conn = self._conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT supplier_name, sku, lead_time_days, reliability "
                    "FROM supplier_lead_times "
                    "WHERE sku = ANY(%s) OR %s IS NULL",
                    (skus or [], skus),
                )
                result: dict[str, list[dict]] = {}
                for row in cur.fetchall():
                    result.setdefault(row["sku"], []).append(dict(row))
                return result
        finally:
            conn.close()

    async def _direct_reorder_analysis(self) -> list[dict]:
        import psycopg2.extras
        conn = self._conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT s.sku, s.current_quantity,
                           COALESCE(AVG(sh.quantity), 0) AS avg_daily_demand,
                           COALESCE(MIN(slt.lead_time_days), 14) AS lead_time_days
                    FROM stock_levels s
                    LEFT JOIN sales_history sh ON sh.sku = s.sku
                        AND sh.sale_date >= CURRENT_DATE - INTERVAL '30 days'
                    LEFT JOIN supplier_lead_times slt ON slt.sku = s.sku
                    GROUP BY s.sku, s.current_quantity
                    ORDER BY s.sku
                """)
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    async def _direct_insert_po(self, po: dict) -> bool:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO purchase_orders "
                    "(audit_id, supplier_name, sku, quantity, unit_price, "
                    "total_cost, lead_time_days, status) "
                    "VALUES (%(audit_id)s, %(supplier_name)s, %(sku)s, "
                    "%(quantity)s, %(unit_price)s, %(total_cost)s, "
                    "%(lead_time_days)s, %(status)s)",
                    po,
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    # ── mock ────────────────────────────────────────────

    def _mock_stock_levels(self, skus: list[str] | None) -> dict[str, int]:
        products = skus or [
            "SKU-A100", "SKU-B200", "SKU-C300", "SKU-D400", "SKU-E500",
        ]
        return {sku: random.randint(0, 100) for sku in products}

    def _mock_sales_history(self, skus: list[str] | None, days: int) -> dict[str, list[dict]]:
        import datetime
        products = skus or [
            "SKU-A100", "SKU-B200", "SKU-C300", "SKU-D400", "SKU-E500",
        ]
        result: dict[str, list[dict]] = {}
        for sku in products:
            records = []
            for d in range(days):
                if random.random() > 0.7:
                    date = datetime.date.today() - datetime.timedelta(days=d)
                    records.append({
                        "sku": sku,
                        "sale_date": date.isoformat(),
                        "quantity": random.randint(1, 20),
                        "unit_price": round(random.uniform(5, 50), 2),
                    })
            result[sku] = records
        return result

    def _mock_supplier_lead_times(self, skus: list[str] | None) -> dict[str, list[dict]]:
        suppliers = {
            "SKU-A100": [
                {"supplier_name": "GlobalSupply Co.", "lead_time_days": 7, "reliability": 0.92},
            ],
            "SKU-B200": [
                {"supplier_name": "Bulk Distributors Inc.",
                 "lead_time_days": 14, "reliability": 0.95},
            ],
            "SKU-C300": [
                {"supplier_name": "GlobalSupply Co.", "lead_time_days": 7, "reliability": 0.92},
            ],
            "SKU-D400": [
                {"supplier_name": "FastShip Logistics", "lead_time_days": 3, "reliability": 0.88},
            ],
            "SKU-E500": [
                {"supplier_name": "EconoParts Ltd.", "lead_time_days": 10, "reliability": 0.78},
            ],
        }
        if skus:
            return {s: suppliers.get(s, []) for s in skus}
        return suppliers

    def _mock_reorder_analysis(self) -> list[dict]:
        return [
            {"sku": "SKU-A100", "current_quantity": 25,
             "avg_daily_demand": 5.0, "lead_time_days": 7},
            {"sku": "SKU-B200", "current_quantity": 120,
             "avg_daily_demand": 12.0, "lead_time_days": 14},
            {"sku": "SKU-C300", "current_quantity": 8,
             "avg_daily_demand": 3.0, "lead_time_days": 7},
            {"sku": "SKU-D400", "current_quantity": 60,
             "avg_daily_demand": 8.0, "lead_time_days": 3},
            {"sku": "SKU-E500", "current_quantity": 3,
             "avg_daily_demand": 2.0, "lead_time_days": 10},
        ]


_db_client: DatabaseClient | None = None


def get_db_client() -> DatabaseClient:
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client
