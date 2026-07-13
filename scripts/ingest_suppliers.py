"""Ingest supplier documents into the vector knowledge base."""

import asyncio
import sys

from src.ingestion.pipeline import ingest_directory


async def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/suppliers"
    collection = sys.argv[2] if len(sys.argv) > 2 else "knowledge_base"
    count = await ingest_directory(path, collection)
    print(f"Ingested {count} nodes into collection '{collection}'.")


if __name__ == "__main__":
    asyncio.run(main())
