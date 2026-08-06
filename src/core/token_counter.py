import tiktoken

from src.core.tracing import traceable

_ENCODING = tiktoken.get_encoding("cl100k_base")


@traceable(name="count_tokens")
def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


@traceable(name="truncate_to_tokens")
def truncate_to_tokens(text: str, max_tokens: int) -> str:
    tokens = _ENCODING.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return _ENCODING.decode(tokens[:max_tokens])
