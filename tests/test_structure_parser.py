"""
Validation tests for Structure Parser module.
Tests deterministic section detection, clause hierarchy, parent-child nesting, page bounds, and annexes.
"""

import pytest
from ai.ingestion.structure_parser import StructureParser, parse_structure


def test_structure_parser_section_and_annex_detection():
    """Verify detection of major Indian Standard sections, annexes, and schedules."""
    pages = [
        {
            "page_number": 1,
            "text": "IS 16102 (Part 1) : 2012\n1 SCOPE\n1.1 This standard specifies safety.\n2 REFERENCES\nIS 15885",
        },
        {
            "page_number": 2,
            "text": "3 TERMINOLOGY\n3.1 Self-ballasted lamp definition.\nSCHEDULE\nGoods requiring registration.",
        },
        {
            "page_number": 3,
            "text": "ANNEX A\nGUIDELINES FOR TESTING\nNormative testing details.",
        },
    ]

    struct = parse_structure(pages)

    assert len(struct["sections"]) >= 3
    section_titles = [s["title"].upper() for s in struct["sections"]]
    assert any("SCOPE" in t for t in section_titles)
    assert any("REFERENCES" in t for t in section_titles)
    assert any("TERMINOLOGY" in t for t in section_titles)

    assert len(struct["annexes"]) == 1
    assert "ANNEX A" in struct["annexes"][0]["annex_id"]
    assert struct["annexes"][0]["page_start"] == 3
    assert struct["annexes"][0]["page_end"] == 3


def test_clause_hierarchical_nesting_and_depth():
    """Verify that multi-level clause structures nest properly with correct depth."""
    pages = [
        {
            "page_number": 5,
            "text": "6 MARKING\n6.1 Mandatory Markings\n6.1.1 Wattage\n6.1.2 Voltage\n6.2 Packaging",
        }
    ]

    struct = parse_structure(pages)
    assert len(struct["clauses"]) >= 1

    clause_6 = next((c for c in struct["clauses"] if c["clause_number"] == "6"), None)
    assert clause_6 is not None
    assert clause_6["depth"] == 1

    sub_nums = [c["clause_number"] for c in clause_6["subclauses"]]
    assert "6.1" in sub_nums
    assert "6.2" in sub_nums

    clause_61 = next(c for c in clause_6["subclauses"] if c["clause_number"] == "6.1")
    assert clause_61["depth"] == 2
    assert len(clause_61["subclauses"]) == 2
    assert clause_61["subclauses"][0]["clause_number"] == "6.1.1"
    assert clause_61["subclauses"][1]["clause_number"] == "6.1.2"


def test_clause_page_boundaries_and_refs():
    """Verify that multi-page clauses accurately track start, end, and page_refs."""
    pages = [
        {"page_number": 10, "text": "8 INSULATION RESISTANCE\n8.1 Start of test on page 10."},
        {"page_number": 11, "text": "8.1 Continued test details on page 11."},
        {"page_number": 12, "text": "8.1 Final requirements on page 12.\n8.2 Electric strength."},
    ]

    struct = parse_structure(pages)
    clause_8 = next(c for c in struct["clauses"] if c["clause_number"] == "8")
    assert clause_8["page_start"] == 10
    assert clause_8["page_end"] == 12
    assert clause_8["page_refs"] == [10, 11, 12]

    clause_81 = next(c for c in clause_8["subclauses"] if c["clause_number"] == "8.1")
    assert clause_81["page_start"] == 10
    assert clause_81["page_end"] == 12
    assert clause_81["page_refs"] == [10, 11, 12]
