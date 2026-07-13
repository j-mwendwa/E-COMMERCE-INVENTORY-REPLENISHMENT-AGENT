"""Evaluation harness for the inventory replenishment agent."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def run_rag_pipeline():
    print("RAG pipeline evaluation placeholder")
    return {"pipeline": "rag", "score": 0.0}


async def run_agent_pipeline():
    print("Agent pipeline evaluation placeholder")
    return {"pipeline": "agent", "score": 0.0}


async def main():
    parser = argparse.ArgumentParser(description="Run evaluation pipelines")
    parser.add_argument("--pipeline", choices=["rag", "agent"], required=True)
    args = parser.parse_args()

    if args.pipeline == "rag":
        result = await run_rag_pipeline()
    else:
        result = await run_agent_pipeline()

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
