"""Print the full context that would be sent to the LLM for a given message."""

import asyncio
import json
import sys

from src.core.context_assembler import ContextAssembler
from src.core.prompt_manager import load_prompt_from_config


async def main():
    message = " ".join(sys.argv[1:]) or "Run a full inventory audit for all SKUs."
    assembler = ContextAssembler()
    system_prompt = load_prompt_from_config("system/demand_analyst")

    context = assembler.build(
        system_prompt=system_prompt,
        entity_memory={"last_audit": "2026-07-12", "preferred_supplier": "GlobalSupply Co."},
        conversation_summary="Previous audit found deficits in SKU-A100, SKU-C300.",
        retrieved_docs=[
            "GlobalSupply Co. lead time: 7 days, reliability: 0.92",
            "FastShip Logistics lead time: 3 days, reliability: 0.88",
        ],
    )

    print(json.dumps({"context": context}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
