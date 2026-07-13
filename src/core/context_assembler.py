import structlog

from src.core.token_counter import count_tokens, truncate_to_tokens

log = structlog.get_logger()


class ContextAssembler:
    def __init__(self, target_tokens: int = 8000):
        self.target_tokens = target_tokens

    def build(
        self,
        system_prompt: str,
        entity_memory: dict[str, str] | None = None,
        conversation_summary: str | None = None,
        retrieved_docs: list[str] | None = None,
    ) -> str:
        parts: list[str] = [system_prompt]

        if entity_memory:
            memory_block = "<entity_memory>\n" + "\n".join(
                f"- {k}: {v}" for k, v in entity_memory.items()
            ) + "\n</entity_memory>"
            parts.append(memory_block)

        if conversation_summary:
            summary_block = (
                f"<conversation_summary>\n{conversation_summary}\n</conversation_summary>"
            )
            parts.append(summary_block)

        if retrieved_docs:
            docs_joined = "\n---\n".join(retrieved_docs)
            docs_block = f"<retrieved_knowledge>\n{docs_joined}\n</retrieved_knowledge>"
            parts.append(docs_block)

        context = "\n\n".join(parts)
        total_tokens = count_tokens(context)

        if total_tokens > self.target_tokens and retrieved_docs:
            overflow = total_tokens - self.target_tokens
            trimmed_docs = list(retrieved_docs)
            while overflow > 0 and trimmed_docs:
                removed = trimmed_docs.pop()
                overflow -= count_tokens(removed)
            trimmed_joined = "\n---\n".join(trimmed_docs)
            docs_block = f"<retrieved_knowledge>\n{trimmed_joined}\n</retrieved_knowledge>"
            parts = [system_prompt]
            if entity_memory:
                parts.append(
                    "<entity_memory>\n" + "\n".join(
                        f"- {k}: {v}" for k, v in entity_memory.items()
                    ) + "\n</entity_memory>"
                )
            if conversation_summary:
                summary_block = (
                    f"<conversation_summary>\n{conversation_summary}\n</conversation_summary>"
                )
                parts.append(summary_block)
            parts.append(docs_block)
            context = "\n\n".join(parts)
            context = truncate_to_tokens(context, self.target_tokens)
            total_tokens = count_tokens(context)

        log.info(
            "context_assembled",
            total_tokens=total_tokens,
            target_tokens=self.target_tokens,
            has_memory=bool(entity_memory),
            has_summary=bool(conversation_summary),
            doc_count=len(retrieved_docs or []),
        )

        return context
