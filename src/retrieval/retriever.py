from src.config import cfg
from src.core.tracing import traceable
from src.vectordb.factory import get_vector_store

_RETRIEVER = None


class LlamaIndexRetriever:
    def __init__(self, collection: str = "knowledge_base"):
        self.collection = collection
        self.vector_store = get_vector_store(collection)
        self.top_k = cfg.get("retrieval", {}).get("top_k", 5)
        self.cutoff = cfg.get("retrieval", {}).get("similarity_cutoff", 0.7)

    @traceable(name="retriever.retrieve")
    def retrieve(self, query: str) -> list[str]:
        try:
            results = self.vector_store.similarity_search_with_score(query, k=self.top_k)
            docs = []
            for doc, score in results:
                if score >= self.cutoff:
                    docs.append(doc.page_content)
            return docs
        except Exception:
            return []


def get_retriever(collection: str = "knowledge_base") -> LlamaIndexRetriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = LlamaIndexRetriever(collection)
    return _RETRIEVER
