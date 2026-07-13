import os
from pathlib import Path

import structlog
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import ROOT_DIR, cfg
from src.vectordb.chroma_store import get_chroma_store

log = structlog.get_logger()

_ALLOWED_INGEST_ROOTS = (ROOT_DIR / "data",)


def _safe_file_list(directory: Path) -> list[Path]:
    resolved = directory.resolve()
    if not any(str(resolved).startswith(str(root.resolve())) for root in _ALLOWED_INGEST_ROOTS):
        raise PermissionError(f"Ingest path {directory} is not under allowed roots")

    files = []
    for root, _dirs, fnames in os.walk(directory, followlinks=False):
        for fname in fnames:
            files.append(Path(root) / fname)
    return files


async def ingest_directory(path: str, collection: str = "knowledge_base") -> int:
    dir_path = Path(path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Ingest path does not exist: {path}")

    _safe_file_list(dir_path)

    reader = SimpleDirectoryReader(input_dir=str(dir_path))
    documents = reader.load_data()
    log.info("documents_loaded", count=len(documents))

    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        embed_batch_size=32,
    )

    chroma_collection = get_chroma_store(collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(
                chunk_size=cfg.get("ingestion", {}).get("chunk_size", 512),
                chunk_overlap=cfg.get("ingestion", {}).get("chunk_overlap", 64),
            ),
            embed_model,
        ],
        vector_store=vector_store,
    )

    nodes = pipeline.run(documents=documents)
    log.info("ingestion_complete", nodes_inserted=len(nodes), collection=collection)
    return len(nodes)
