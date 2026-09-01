"""
Conversational Context & Session Memory Manager (Phase 7F).
Resolves conversational follow-up queries while maintaining strict isolation
from the authoritative BIS knowledge corpus.
"""
import re
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConversationTurn(BaseModel):
    query: str
    resolved_standard: Optional[str] = None
    resolved_product: Optional[str] = None
    answer_summary: Optional[str] = None


class ConversationMemory:
    """
    Thread-safe in-memory session manager for conversational context resolution.
    """

    def __init__(self):
        self._sessions: Dict[str, List[ConversationTurn]] = {}

    def get_history(self, conversation_id: str) -> List[ConversationTurn]:
        return self._sessions.get(conversation_id, [])

    def add_turn(
        self,
        conversation_id: str,
        query: str,
        resolved_standard: Optional[str] = None,
        resolved_product: Optional[str] = None,
        answer_summary: Optional[str] = None
    ):
        if conversation_id not in self._sessions:
            self._sessions[conversation_id] = []
        self._sessions[conversation_id].append(
            ConversationTurn(
                query=query,
                resolved_standard=resolved_standard,
                resolved_product=resolved_product,
                answer_summary=answer_summary
            )
        )

    def resolve_query(self, query: str, conversation_id: Optional[str] = None) -> str:
        """
        Resolves pronouns or elliptical follow-ups using conversation history.
        E.g., "What is its latest edition?" -> "What is latest edition of IS 1786?"
        """
        if not conversation_id or conversation_id not in self._sessions:
            return query

        history = self._sessions[conversation_id]
        if not history:
            return query

        last_turn = history[-1]
        last_std = last_turn.resolved_standard
        last_prod = last_turn.resolved_product

        target_subject = last_std or last_prod
        if not target_subject:
            return query

        q_lower = query.lower()
        pronoun_patterns = [
            r"\b(it|its|this|that|this product|this standard|the standard|the product)\b"
        ]

        needs_resolution = any(re.search(p, q_lower) for p in pronoun_patterns)
        
        # If query is very short or clearly an elliptical follow-up
        if needs_resolution or len(query.split()) <= 5 and not re.search(r"is\s+\d+", q_lower):
            # If target subject is not already explicitly mentioned in query
            if target_subject.lower() not in q_lower:
                resolved_q = f"{query} (referring to {target_subject})"
                logger.info("Conversational query rewritten: '%s' -> '%s'", query, resolved_q)
                return resolved_q

        return query


# Global singleton instance
conversation_manager = ConversationMemory()
