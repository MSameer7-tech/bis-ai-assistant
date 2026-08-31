"""
Phase 2E Unified RAG Pipeline: Coordinates structured query parsing, parameter-aware retrieval,
context building, generation, citation verification, compliance guardrails, and hard abstention gating.
"""
import re
import logging
from typing import Optional, List, Dict, Any
from ai.rag.models import RAGAnswer, RetrievedChunk, Citation, GuardrailResult, AbstentionReason
from ai.rag.retriever import RAGRetriever
from ai.rag.context_builder import ContextBuilder
from ai.rag.prompt import BIS_SYSTEM_PROMPT, build_user_prompt
from ai.rag.generator import BaseLLMProvider, get_llm_provider
from ai.rag.citation import CitationExtractor
from ai.rag.guardrails import ComplianceGuardrails
from ai.rag.answer import AnswerFormatter
from ai.retrieval.query_parser import QueryParser, StructuredQuery, CANONICAL_PARAMETER_ALIASES

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-End Grounded RAG Pipeline for BIS standards QA.
    Enforces the 'Zero-Ungrounded-Answer' principle with complete provenance and hard abstention gates.
    """

    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        context_builder: Optional[ContextBuilder] = None,
        generator: Optional[BaseLLMProvider] = None,
        citation_extractor: Optional[CitationExtractor] = None,
        guardrails: Optional[ComplianceGuardrails] = None,
        formatter: Optional[AnswerFormatter] = None
    ):
        self.retriever = retriever or RAGRetriever()
        self.context_builder = context_builder or ContextBuilder()
        self.generator = generator or get_llm_provider()
        self.citation_extractor = citation_extractor or CitationExtractor()
        self.guardrails = guardrails or ComplianceGuardrails()
        self.formatter = formatter or AnswerFormatter()

    def answer_question(
        self,
        query: str,
        top_k: int = 5,
        as_of_date: Optional[str] = None,
        candidate_k: int = 25
    ) -> RAGAnswer:
        """
        Executes the complete grounded answer lifecycle for a user question.
        """
        logger.info("Executing RAG Pipeline for query: '%s' (as_of=%s)", query, as_of_date)
        temporal_label = as_of_date or "Current Effective Edition"

        # 1. Structured Query Parsing (Step 2E.1)
        sq: StructuredQuery = QueryParser.parse(query, as_of_date=as_of_date)

        # 2. Out-of-Scope Pre-Check (Step 2E.9)
        if sq.intent == "OUT_OF_SCOPE":
            return RAGAnswer(
                query=query,
                answer="I could not find sufficient information in the retrieved BIS standards corpus to answer this question.",
                citations=[],
                retrieved_chunks=[],
                confidence=1.0,
                temporal_context=temporal_label,
                refusal_reason="Query is out of scope of the technical BIS standards corpus.",
                abstention_type=AbstentionReason.OUT_OF_SCOPE,
                guardrail_result=GuardrailResult(
                    passed=True,
                    grounding_confidence=1.0,
                    refusal_required=True,
                    abstention_reason=AbstentionReason.OUT_OF_SCOPE,
                    warnings=["Query answered with grounded refusal due to out-of-scope domain."]
                ),
                technical_details={}
            )

        # 3. Hybrid Parameter-Aware Retrieval
        chunks: List[RetrievedChunk] = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            as_of_date=as_of_date,
            candidate_k=candidate_k
        )

        if not chunks:
            return RAGAnswer(
                query=query,
                answer="I could not find sufficient information in the retrieved BIS standards corpus to answer this question.",
                citations=[],
                retrieved_chunks=[],
                confidence=1.0,
                temporal_context=temporal_label,
                refusal_reason="No relevant BIS standard chunks found.",
                abstention_type=AbstentionReason.INSUFFICIENT_EVIDENCE,
                guardrail_result=GuardrailResult(
                    passed=True,
                    grounding_confidence=1.0,
                    refusal_required=True,
                    abstention_reason=AbstentionReason.INSUFFICIENT_EVIDENCE
                ),
                technical_details={}
            )

        # 4. Parameter Evidence Pre-Validation (Step 2E.4)
        if sq.intent == "PARAMETER_QUERY" and sq.parameter:
            aliases = CANONICAL_PARAMETER_ALIASES.get(sq.parameter, [sq.parameter])
            all_text_lower = " ".join(c.text for c in chunks).lower()
            param_words = sq.parameter.replace("_", " ").split()
            parameter_found = (
                any(alias in all_text_lower for alias in aliases)
                or any(w in all_text_lower for w in param_words if len(w) > 3)
                or (sq.standard_code and any(re.sub(r"[\s:]+", "", sq.standard_code.lower()) in re.sub(r"[\s:]+", "", c.standard_number.lower()) for c in chunks))
            )
            
            # If parameter is completely absent from all retrieved chunks -> ABSTAIN with WRONG_PARAMETER
            if not parameter_found:
                param_display = sq.parameter.replace("_", " ")
                prod_display = f" for {sq.product}" if sq.product else ""
                refusal_msg = f"I could not find a verified {param_display} requirement in the retrieved BIS evidence{prod_display}."
                return RAGAnswer(
                    query=query,
                    answer=refusal_msg,
                    citations=[],
                    retrieved_chunks=chunks,
                    confidence=0.8,
                    temporal_context=temporal_label,
                    refusal_reason=f"Retrieved standard lacks verified evidence for parameter '{param_display}'.",
                    abstention_type=AbstentionReason.WRONG_PARAMETER,
                    guardrail_result=GuardrailResult(
                        passed=True,
                        grounding_confidence=0.8,
                        refusal_required=True,
                        abstention_reason=AbstentionReason.WRONG_PARAMETER,
                        warnings=[f"Parameter '{param_display}' not present in evidence chunks."]
                    ),
                    technical_details={}
                )

        # 5. Build Structured Context
        context = self.context_builder.build_context(chunks)

        # 6. Build Grounded Prompts
        user_prompt = build_user_prompt(query, context, as_of_date)

        # 7. Generate Grounded Answer
        draft_answer = self.generator.generate_answer(
            system_prompt=BIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            context=context,
            query=query
        )

        # 8. Extract and Validate Citations
        citations: List[Citation] = self.citation_extractor.extract_citations(
            answer_text=draft_answer,
            retrieved_chunks=chunks
        )

        # 9. Apply Safety & Compliance Guardrails
        guard_result: GuardrailResult = self.guardrails.verify(
            query=query,
            answer_text=draft_answer,
            retrieved_chunks=chunks,
            citations=citations
        )

        # 10. Hard Guardrail Enforcement (Step 2E.7)
        if not guard_result.passed:
            # Block ungrounded answer and replace with hard abstention
            violations_str = "; ".join(guard_result.violations)
            draft_answer = f"I could not verify the technical parameter claims in the retrieved BIS evidence ({violations_str})."
            citations = []
            abstention_type = guard_result.abstention_reason or AbstentionReason.UNSUPPORTED_NUMERICAL_CLAIM
            refusal_reason = f"Hard guardrail block: {violations_str}"
        else:
            abstention_type = guard_result.abstention_reason
            refusal_reason = "Insufficient evidence." if guard_result.refusal_required else None

        rag_answer = RAGAnswer(
            query=query,
            answer=draft_answer,
            citations=citations,
            retrieved_chunks=chunks,
            confidence=guard_result.grounding_confidence,
            temporal_context=temporal_label,
            refusal_reason=refusal_reason,
            abstention_type=abstention_type,
            guardrail_result=guard_result,
            technical_details={}
        )

        logger.info(
            "RAG Pipeline finished: %d citations (%d verified), confidence=%.2f, passed=%s",
            len(citations),
            sum(1 for c in citations if c.verified),
            rag_answer.confidence,
            guard_result.passed
        )

        return rag_answer
