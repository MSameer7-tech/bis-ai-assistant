import pytest
from ai.rag.conversation import ConversationMemory


def test_conversation_resolution_pronoun():
    memory = ConversationMemory()
    conv_id = "sess-123"
    
    # Turn 1
    memory.add_turn(
        conversation_id=conv_id,
        query="What is the scope of IS 1786?",
        resolved_standard="IS 1786",
        resolved_product="TMT Bars",
        answer_summary="IS 1786 specifies high strength deformed steel bars."
    )

    # Turn 2: Follow-up with pronoun
    resolved = memory.resolve_query("What is its yield strength?", conversation_id=conv_id)
    assert "IS 1786" in resolved or "TMT Bars" in resolved


def test_conversation_resolution_independent():
    memory = ConversationMemory()
    conv_id = "sess-456"
    
    memory.add_turn(
        conversation_id=conv_id,
        query="What is IS 374?",
        resolved_standard="IS 374",
        resolved_product="Ceiling Fans"
    )

    # Independent explicit query should remain untouched
    resolved = memory.resolve_query("What is IS 2925 for safety helmets?", conversation_id=conv_id)
    assert resolved == "What is IS 2925 for safety helmets?"
