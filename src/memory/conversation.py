from typing import Any

import structlog
from langchain_core.prompts import ChatPromptTemplate

from src.config import cfg, settings
from src.core.prompt_manager import load_prompt

log = structlog.get_logger()

_SUMMARIZER: Any | None = None


def _get_summarizer() -> Any:
    global _SUMMARIZER
    if _SUMMARIZER is None:
        model_name = str(cfg.get("llm", {}).get("default_model", "gemini-1.5-flash"))
        if model_name.lower().startswith("gemini"):
            from langchain_google_genai import ChatGoogleGenerativeAI

            _SUMMARIZER = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.0,
                google_api_key=settings.google_api_key,
            )
        else:
            from langchain_anthropic import ChatAnthropic

            _SUMMARIZER = ChatAnthropic(
                model=model_name,
                temperature=0.0,
                api_key=settings.anthropic_api_key,
            )
    return _SUMMARIZER


async def summarize_history(previous_summary: str | None, transcript: str) -> str:
    summarizer = _get_summarizer()
    system_prompt = load_prompt("summarizer_system")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Previous summary:\n{summary}\n\nNew transcript:\n{transcript}"),
        ]
    )

    chain = prompt | summarizer
    result = await chain.ainvoke(
        {
            "summary": previous_summary or "No prior conversation.",
            "transcript": transcript,
        }
    )

    summary = result.content.strip()
    log.info("conversation_summarized", summary_length=len(summary))
    return summary
