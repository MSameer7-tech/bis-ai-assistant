import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from ai.retrieval.structured_retrieval_models import RetrievalResult, RetrievalSourceType

class StandardsMetadataIndex:
    """
    Deterministic read-only index over authoritative BIS standards metadata.
    Does not use LLMs or semantic vectors.
    """
    def __init__(self, metadata_path: Optional[Path] = None):
        self.metadata_path = metadata_path or Path(__file__).resolve().parent.parent.parent / "data" / "catalog" / "standards" / "standards_metadata.jsonl"
        self.records_by_id: Dict[str, Dict[str, Any]] = {}
        self.records_by_base: Dict[str, List[Dict[str, Any]]] = {}
        self._load_index()

    def _load_index(self):
        if not self.metadata_path.exists():
            return

        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            for line in f:
                rec = json.loads(line)
                internal_id = rec.get("internal_bis_id")
                if not internal_id:
                    continue
                    
                self.records_by_id[internal_id] = rec
                
                # Parse base, part, section, year for deterministic family lookups
                raw_std = rec.get("standard_number", "")
                base_match = re.search(r'(?:IS\s*/\s*IEC|IS|IEC)?\s*([0-9]{3,})', raw_std, re.IGNORECASE)
                if base_match:
                    base_num = base_match.group(1)
                    if base_num not in self.records_by_base:
                        self.records_by_base[base_num] = []
                    self.records_by_base[base_num].append(rec)

    def _to_result(self, rec: Dict[str, Any], score: float = 1.0) -> RetrievalResult:
        return RetrievalResult(
            source_type=RetrievalSourceType.STANDARD_METADATA,
            record_id=rec["internal_bis_id"],
            score=score,
            standard_number=rec["standard_number"],
            title=rec.get("title", ""),
            text=f"{rec.get('standard_number')} - {rec.get('title')}. Status: {rec.get('status')}",
            metadata={
                "internal_bis_id": rec["internal_bis_id"],
                "status": rec.get("status", ""),
                "technical_committee": rec.get("technical_committee", ""),
                "reaffirmed_year": rec.get("reaffirmed_year", ""),
                "amendments": rec.get("amendments", [])
            },
            provenance=rec.get("source", {})
        )

    def get_by_internal_id(self, internal_id: str) -> Optional[RetrievalResult]:
        rec = self.records_by_id.get(internal_id)
        if rec:
            return self._to_result(rec, score=1.0)
        return None

    def exact_lookup(self, query: str) -> List[RetrievalResult]:
        """Looks up by explicit string match or exact base/part constraint."""
        q_clean = query.strip().lower()
        
        # Check explicit ID match first (e.g. standard_number exactly)
        results = []
        for rec in self.records_by_id.values():
            if rec.get("standard_number", "").strip().lower() == q_clean:
                results.append(self._to_result(rec, score=1.0))
        if results:
            return results

        # Try deterministic hierarchical matching
        base_match = re.search(r'(?:is\s*/\s*iec|is|iec)?\s*([0-9]{3,})', q_clean)
        if not base_match:
            return []
            
        base_num = base_match.group(1)
        family = self.records_by_base.get(base_num, [])
        if not family:
            return []

        part_match = re.search(r'part\s*([0-9a-z]+)', q_clean)
        sec_match = re.search(r'sec(?:tion)?\s*([0-9a-z]+)', q_clean)
        year_match = re.search(r':\s*([12][0-9]{3})', q_clean)

        cand_part = part_match.group(1) if part_match else None
        cand_sec = sec_match.group(1) if sec_match else None
        cand_year = year_match.group(1) if year_match else None

        matches = []
        for f in family:
            f_raw = f.get("standard_number", "").lower()
            f_part_match = re.search(r'part\s*([0-9a-z]+)', f_raw)
            f_part = f_part_match.group(1) if f_part_match else None
            
            # If candidate specified a part, only allow exact part match
            if cand_part and (not f_part or f_part != cand_part):
                continue
                    
            f_sec_match = re.search(r'sec(?:tion)?\s*([0-9a-z]+)', f_raw)
            f_sec = f_sec_match.group(1) if f_sec_match else None
            if cand_sec and (not f_sec or f_sec != cand_sec):
                continue
            
            f_year_match = re.search(r':\s*([12][0-9]{3})', f_raw)
            f_year = f_year_match.group(1) if f_year_match else None
            if cand_year and (not f_year or f_year != cand_year):
                continue
                    
            matches.append(f)

        # If candidate didn't specify a part, but all matches have parts, it's ambiguous.
        # But if there's a record with NO part, prefer that one.
        if not cand_part:
            no_part_matches = [m for m in matches if not re.search(r'part\s*[0-9a-z]+', m.get("standard_number", "").lower())]
            if no_part_matches:
                matches = no_part_matches

        return [self._to_result(m, score=1.0) for m in matches]

    def lexical_search(self, query: str) -> List[RetrievalResult]:
        """Basic token overlap search against titles."""
        q_tokens = set(re.findall(r'\w+', query.lower()))
        if not q_tokens:
            return []
            
        scored = []
        for rec in self.records_by_id.values():
            title = rec.get("title", "").lower()
            t_tokens = set(re.findall(r'\w+', title))
            if not t_tokens:
                continue
                
            overlap = len(q_tokens.intersection(t_tokens))
            if overlap > 0:
                score = overlap / len(q_tokens)
                if score >= 0.3: # Threshold
                    scored.append((score, rec))
                    
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._to_result(r, score=s) for s, r in scored[:10]]
