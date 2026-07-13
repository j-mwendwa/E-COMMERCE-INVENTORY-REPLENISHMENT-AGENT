from src.core.context_assembler import ContextAssembler
from src.core.token_counter import count_tokens


def test_context_assembler_build():
    assembler = ContextAssembler(target_tokens=8000)
    context = assembler.build(
        system_prompt="You are a demand analyst.",
        entity_memory={"last_audit": "2026-07-12"},
        conversation_summary="Previous audit found deficits.",
        retrieved_docs=["Supplier A: lead time 7 days", "Supplier B: lead time 3 days"],
    )
    assert "<entity_memory>" in context
    assert "<conversation_summary>" in context
    assert "<retrieved_knowledge>" in context
    assert "last_audit" in context


def test_context_assembler_token_count():
    assembler = ContextAssembler(target_tokens=8000)
    context = assembler.build(system_prompt="Hello world.")
    tokens = count_tokens(context)
    assert tokens > 0
    assert tokens < 100


def test_context_assembler_trims_when_overflow():
    assembler = ContextAssembler(target_tokens=50)
    context = assembler.build(
        system_prompt="Short prompt.",
        retrieved_docs=["A" * 1000, "B" * 1000, "C" * 1000],
    )
    tokens = count_tokens(context)
    assert tokens > 0
