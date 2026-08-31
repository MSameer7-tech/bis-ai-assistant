"""
Tests for Phase 4 Batch 2: context_builder.py and prompt.py
"""
import pytest
from ai.rag.models import RetrievedChunk
from ai.rag.context_builder import ContextBuilder
from ai.rag.prompt import BIS_SYSTEM_PROMPT, build_user_prompt


def test_context_builder_formats_evidence_and_banners():
    chunks = [
        RetrievedChunk(
            chunk_id="DOC-001-v001::8.1.1::REQ-001",
            document_id="DOC-001",
            version_id="DOC-001-v001",
            source_id="SRC-001",
            standard_number="IS 16102 (Part 1) : 2012",
            clause_number="8.1.1",
            pages=[9],
            chunk_type="requirement",
            normative_force="mandatory",
            temporal_status="current",
            valid_from="2012-08-01",
            score=0.032,
            text="The insulation resistance shall not be less than 4 MΩ.",
            content_hash="abc123hash",
            provenance={"document_id": "DOC-001", "clause": "8.1.1", "pages": [9]}
        ),
        RetrievedChunk(
            chunk_id="DOC-001-v001::Table_3::TAB-001",
            document_id="DOC-001",
            version_id="DOC-001-v001",
            source_id="SRC-001",
            standard_number="IS 16102 (Part 1) : 2012",
            clause_number="9.1",
            pages=[11],
            chunk_type="table",
            normative_force="under_consideration",
            temporal_status="current",
            valid_from="2012-08-01",
            score=0.030,
            text="GX53 | 3.0 Nm | under_consideration",
            content_hash="def456hash",
            provenance={"document_id": "DOC-001", "clause": "9.1", "pages": [11]}
        )
    ]

    builder = ContextBuilder(max_tokens=2000)
    context = builder.build_context(chunks)

    assert len(context.evidence_blocks) == 2
    assert "[EVIDENCE-1]" in context.formatted_prompt_context
    assert "[EVIDENCE-2]" in context.formatted_prompt_context
    assert "IS 16102 (Part 1) : 2012" in context.formatted_prompt_context
    assert "MANDATORY NORMATIVE REQUIREMENT" in context.evidence_blocks[0]
    assert "[PROVISIONAL / UNDER CONSIDERATION - NOT A MANDATORY REQUIREMENT]" in context.evidence_blocks[1]


def test_build_user_prompt():
    chunks = [
        RetrievedChunk(
            chunk_id="DOC-001-v001::8.1.1::REQ-001",
            document_id="DOC-001",
            version_id="DOC-001-v001",
            source_id="SRC-001",
            standard_number="IS 16102 (Part 1) : 2012",
            clause_number="8.1.1",
            pages=[9],
            chunk_type="requirement",
            normative_force="mandatory",
            temporal_status="current",
            valid_from="2012-08-01",
            score=0.032,
            text="The insulation resistance shall not be less than 4 MΩ.",
            content_hash="abc123hash",
            provenance={}
        )
    ]
    context = ContextBuilder().build_context(chunks)
    prompt = build_user_prompt("What is the minimum insulation resistance?", context, as_of_date="2026-08-30")

    assert "USER QUESTION: What is the minimum insulation resistance?" in prompt
    assert "Target Applicable Date: 2026-08-30" in prompt
    assert "[EVIDENCE-1]" in prompt
    assert "IS 16102 (Part 1) : 2012" in prompt
