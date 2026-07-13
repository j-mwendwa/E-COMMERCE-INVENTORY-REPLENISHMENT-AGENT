from langchain_core.tools import tool

from src.tools.registry import register_base_tool


@tool
def knowledge_base_search(question: str) -> str:
    """Search the supplier knowledge base for relevant information."""
    from src.retrieval.retriever import get_retriever

    retriever = get_retriever()
    docs = retriever.retrieve(question)
    if not docs:
        return "No relevant supplier information found."
    return "\n---\n".join(docs)


register_base_tool("knowledge_base_search", knowledge_base_search)
