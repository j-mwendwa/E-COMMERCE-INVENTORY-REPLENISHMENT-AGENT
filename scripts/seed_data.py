"""Seed mock supplier data into the knowledge base for prototyping."""

import asyncio
from pathlib import Path

from src.config import ROOT_DIR
from src.ingestion.pipeline import ingest_directory


async def main():
    suppliers_dir = ROOT_DIR / "data" / "raw" / "suppliers"
    suppliers_dir.mkdir(parents=True, exist_ok=True)

    sample_file = suppliers_dir / "supplier_terms.md"
    if not sample_file.exists():
        sample_file.write_text(
            "# Supplier Terms & Agreements\n\n"
            "## GlobalSupply Co.\n"
            "- SKUs: SKU-A100, SKU-B200, SKU-C300\n"
            "- Lead time: 7 days\n"
            "- Payment terms: Net 30\n"
            "- Minimum order: 50 units (SKU-A100), 100 units (SKU-B200), 25 units (SKU-C300)\n"
            "- Volume discount: 5% for orders over $5,000\n\n"
            "## FastShip Logistics\n"
            "- SKUs: SKU-A100, SKU-D400, SKU-E500\n"
            "- Lead time: 3 days (express)\n"
            "- Payment terms: Net 15\n"
            "- Minimum order: 20 units (SKU-A100), 10 units (SKU-D400), 15 units (SKU-E500)\n"
            "- Premium pricing: +15% for express shipping\n\n"
            "## Bulk Distributors Inc.\n"
            "- SKUs: SKU-B200, SKU-C300, SKU-D400\n"
            "- Lead time: 14 days\n"
            "- Payment terms: Net 45\n"
            "- Minimum order: 500 units (SKU-B200), 200 units (SKU-C300), 50 units (SKU-D400)\n"
            "- Best pricing for bulk orders\n\n"
            "## EconoParts Ltd.\n"
            "- SKUs: SKU-E500, SKU-A100\n"
            "- Lead time: 10 days\n"
            "- Payment terms: Net 30\n"
            "- Minimum order: 30 units (SKU-E500), 100 units (SKU-A100)\n"
            "- Budget-friendly pricing, moderate reliability\n"
        )

    count = await ingest_directory(str(suppliers_dir))
    print(f"Seeded {count} nodes into the knowledge base.")


if __name__ == "__main__":
    asyncio.run(main())
