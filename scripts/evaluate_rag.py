#!/usr/bin/env python3
"""
Comprehensive Phase 2F Extended 105-Question RAG Benchmark Evaluation.
Audits:
1. Standard Identification (15)
2. Product Scope & Applicability (10)
3. Numerical Parameters & Limits (15)
4. Environmental & Test Conditioning (10)
5. Tables & Tolerances (10)
6. Clauses & Hierarchy (10)
7. Revision & Edition Differences (10)
8. Temporal Effective Dates & Versioning (10)
9. QCOs & Gazette Notifications (5)
10. Adversarial / Hallucination Resistance & Refusals (10)
Total: 105 Questions.
"""
import sys
import json
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.rag.pipeline import RAGPipeline

logging.basicConfig(level=logging.WARNING)

BENCHMARK_CASES = [
    # -------------------------------------------------------------------------
    # Category 1: Standard Identification (15 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-001",
        "category": "Std ID - Ceiling Fans",
        "query": "Which Indian Standard specifies electric ceiling fans?",
        "expected_tokens": ["IS 374"],
        "expected_standard": "IS 374",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-002",
        "category": "Std ID - 53 Grade Cement",
        "query": "What standard covers Ordinary Portland Cement 53 Grade?",
        "expected_tokens": ["IS 269"],
        "expected_standard": "IS 269",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-003",
        "category": "Std ID - Motorcycle Helmets",
        "query": "Which BIS standard applies to protective helmets for two wheeler riders?",
        "expected_tokens": ["IS 4151"],
        "expected_standard": "IS 4151",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-004",
        "category": "Std ID - Secondary Lithium Cells",
        "query": "Which Indian standard governs secondary lithium cells and batteries for portable applications?",
        "expected_tokens": ["IS 16046 (Part 2)"],
        "expected_standard": "IS 16046 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-005",
        "category": "Std ID - Packaged Drinking Water",
        "query": "Which standard specifies packaged drinking water other than packaged natural mineral water?",
        "expected_tokens": ["IS 14543"],
        "expected_standard": "IS 14543",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-006",
        "category": "Std ID - Domestic Pressure Cookers",
        "query": "What standard applies to domestic pressure cookers?",
        "expected_tokens": ["IS 2347"],
        "expected_standard": "IS 2347",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-007",
        "category": "Std ID - Safety Footwear",
        "query": "Which Indian Standard specifies safety footwear?",
        "expected_tokens": ["IS 15298 (Part 2)"],
        "expected_standard": "IS 15298 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-008",
        "category": "Std ID - Deformed Steel Bars",
        "query": "Which Indian Standard covers high strength deformed steel bars and wires for concrete reinforcement?",
        "expected_tokens": ["IS 1786"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-009",
        "category": "Std ID - Self-Ballasted LED Lamps",
        "query": "What standard specifies safety requirements for self-ballasted LED lamps for general lighting?",
        "expected_tokens": ["IS 16102 (Part 1)"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-009B",
        "category": "Std ID - LED Performance",
        "query": "Which standard specifies performance requirements for self-ballasted LED lamps?",
        "expected_tokens": ["IS 16102 (Part 2)"],
        "expected_standard": "IS 16102 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-010",
        "category": "Std ID - Domestic LPG Gas Stoves",
        "query": "Which Indian Standard covers domestic gas stoves for use with LPG?",
        "expected_tokens": ["IS 4246"],
        "expected_standard": "IS 4246",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-011",
        "category": "Std ID - Portable Fire Extinguishers",
        "query": "Which standard specifies performance and construction of portable fire extinguishers?",
        "expected_tokens": ["IS 15683"],
        "expected_standard": "IS 15683",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-012",
        "category": "Std ID - Domestic Water Meters",
        "query": "Which Indian Standard covers water meters of domestic type?",
        "expected_tokens": ["IS 779"],
        "expected_standard": "IS 779",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-013",
        "category": "Std ID - PVC Industrial Boots",
        "query": "Which standard covers polyvinyl chloride (PVC) industrial boots?",
        "expected_tokens": ["IS 12254"],
        "expected_standard": "IS 12254",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-014",
        "category": "Std ID - Diagnostic X-Ray Equipment",
        "query": "Which Indian standard covers safety requirements for diagnostic medical X-ray equipment?",
        "expected_tokens": ["IS 7620 (Part 1)"],
        "expected_standard": "IS 7620 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 2: Product Scope & Applicability (10 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-015",
        "category": "Scope - LED Lamp Max Wattage",
        "query": "What is the maximum rated wattage for self-ballasted LED lamps covered under IS 16102 (Part 1)?",
        "expected_tokens": ["60 W"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-016",
        "category": "Scope - LED Lamp Voltage Rating",
        "query": "What is the rated voltage limit for lamps covered under IS 16102 (Part 1)?",
        "expected_tokens": ["250 V", "voltage"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-017",
        "category": "Scope - Pressure Cooker Capacity",
        "query": "What is the scope of nominal capacity of pressure cookers under IS 2347?",
        "expected_tokens": ["pressure cookers"],
        "expected_standard": "IS 2347",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-018",
        "category": "Scope - Helmet Protection Scope",
        "query": "What is the intended scope of protective helmets under IS 4151?",
        "expected_tokens": ["riders", "two wheeler"],
        "expected_standard": "IS 4151",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-019",
        "category": "Scope - Lithium Battery Application",
        "query": "What applications are secondary lithium cells and batteries covered for under IS 16046 (Part 2)?",
        "expected_tokens": ["portable", "applications"],
        "expected_standard": "IS 16046 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-020",
        "category": "Scope - Medical Face Masks",
        "query": "What types of surgical face masks are classified under IS 16289?",
        "expected_tokens": ["Type I", "Type II"],
        "expected_standard": "IS 16289",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-021",
        "category": "Scope - PVC Pipes Application",
        "query": "What is the intended application of unplasticized PVC pipes covered under IS 4985?",
        "expected_tokens": ["potable water"],
        "expected_standard": "IS 4985",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-022",
        "category": "Scope - Steel Structural Grades",
        "query": "What is the scope of hot rolled medium and high tensile structural steel under IS 2062?",
        "expected_tokens": ["structural", "steel"],
        "expected_standard": "IS 2062",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-023",
        "category": "Scope - Water Extinguisher Capacity",
        "query": "What capacity is specified for water type gas cartridge portable fire extinguishers under IS 940?",
        "expected_tokens": ["9", "litre"],
        "expected_standard": "IS 940",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-024",
        "category": "Scope - Full Body Safety Harness",
        "query": "What purpose are industrial safety belts and harnesses specified for under IS 3521 (Part 1)?",
        "expected_tokens": ["fall arrest", "full body harness"],
        "expected_standard": "IS 3521 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 3: Numerical Parameters & Limits (15 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-025",
        "category": "Num - Insulation Resistance",
        "query": "What is the minimum insulation resistance for self-ballasted LED lamps?",
        "expected_tokens": ["4 MΩ"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-026",
        "category": "Num - Fe 500 Yield Stress",
        "query": "What is the minimum yield stress for Fe 500 grade steel bars?",
        "expected_tokens": ["500.0 MPa"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-027",
        "category": "Num - Fe 500D Elongation",
        "query": "What is the minimum percentage elongation for Fe 500D steel bars?",
        "expected_tokens": ["16.0%"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-028",
        "category": "Num - Fe 550D Elongation",
        "query": "What is the minimum elongation for Fe 550D steel bars under IS 1786?",
        "expected_tokens": ["14.5%"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-029",
        "category": "Num - Drinking Water pH",
        "query": "What is the required pH range for packaged drinking water under IS 14543?",
        "expected_tokens": ["6.5 to 8.5"],
        "expected_standard": "IS 14543",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-030",
        "category": "Num - Drinking Water TDS",
        "query": "What is the maximum total dissolved solids (TDS) allowed in packaged drinking water under IS 14543?",
        "expected_tokens": ["500 mg/l"],
        "expected_standard": "IS 14543",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-031",
        "category": "Num - Helmet Drop Deceleration",
        "query": "What is the peak headform deceleration limit during drop test of motorcycle helmets?",
        "expected_tokens": ["300 g"],
        "expected_standard": "IS 4151",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-032",
        "category": "Num - Helmet Mass Limit",
        "query": "What is the maximum permissible mass for motorcycle helmets under IS 4151?",
        "expected_tokens": ["1500 g"],
        "expected_standard": "IS 4151",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-033",
        "category": "Num - Safety Footwear Toecap Impact",
        "query": "What impact energy must steel toecaps withstand in safety footwear under IS 15298 (Part 2)?",
        "expected_tokens": ["200 J"],
        "expected_standard": "IS 15298 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-034",
        "category": "Num - Safety Footwear Clearance",
        "query": "What is the minimum clearance under toecap after impact test for size 8 safety footwear?",
        "expected_tokens": ["14.0 mm"],
        "expected_standard": "IS 15298 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-035",
        "category": "Num - Pressure Cooker Burst Pressure",
        "query": "What is the minimum hydraulic proof burst pressure for domestic pressure cookers under IS 2347?",
        "expected_tokens": ["3.0 bar"],
        "expected_standard": "IS 2347",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-036",
        "category": "Num - Gas Stove Thermal Efficiency",
        "query": "What is the minimum thermal efficiency required for domestic LPG gas stoves under IS 4246?",
        "expected_tokens": ["68%"],
        "expected_standard": "IS 4246",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-037",
        "category": "Num - Industrial Helmet Shock Force",
        "query": "What is the maximum transmitted force allowed in the shock absorption test of industrial safety helmets?",
        "expected_tokens": ["5.0 kN"],
        "expected_standard": "IS 2925",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-038",
        "category": "Num - FFP2 Filtration Efficiency",
        "query": "What is the minimum filtration efficiency for FFP2 masks under IS 9473?",
        "expected_tokens": ["94%"],
        "expected_standard": "IS 9473",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-039",
        "category": "Num - BFE Surgical Mask Type II",
        "query": "What is the minimum bacterial filtration efficiency (BFE) for Type II medical face masks under IS 16289?",
        "expected_tokens": ["98%"],
        "expected_standard": "IS 16289",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 4: Environmental & Test Conditioning (10 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-040",
        "category": "Env - Humidity Treatment Duration",
        "query": "What is the duration of humidity treatment before insulation resistance testing in IS 16102 (Part 1)?",
        "expected_tokens": ["48 h"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-041",
        "category": "Env - Humidity Cabinet RH Range",
        "query": "What relative humidity range is maintained in the humidity cabinet during insulation conditioning?",
        "expected_tokens": ["91", "95"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-042",
        "category": "Env - Humidity Temperature Range",
        "query": "What temperature range is maintained in the humidity cabinet for LED lamp preconditioning?",
        "expected_tokens": ["25°C", "35°C"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-043",
        "category": "Env - LED Lumen Maintenance Duration",
        "query": "What test duration is specified for 2000 h lumen maintenance test under IS 16102 (Part 2)?",
        "expected_tokens": ["2000 h"],
        "expected_standard": "IS 16102 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-044",
        "category": "Env - Water Bath Test Temperature for LPG Can",
        "query": "What water bath temperature is used for leakage testing of non-refillable LPG containers under IS 13745?",
        "expected_tokens": ["55°C"],
        "expected_standard": "IS 13745",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-045",
        "category": "Env - Safety Harness Static Test Duration",
        "query": "For how long must the 15 kN static test load be sustained on safety harnesses under IS 3521 (Part 1)?",
        "expected_tokens": ["3 minutes"],
        "expected_standard": "IS 3521 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-046",
        "category": "Env - Ceiling Fan Air Delivery Test Chamber",
        "query": "Under what test chamber conditions is air delivery tested for electric ceiling fans?",
        "expected_tokens": ["IS 374"],
        "expected_standard": "IS 374",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-047",
        "category": "Env - Rebar Total Elongation at Max Force Gauge",
        "query": "What gauge length condition is used for total elongation at maximum force (Agt) testing?",
        "expected_tokens": ["IS 1786"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-048",
        "category": "Env - Fire Coupling Proof Pressure Duration",
        "query": "For how many minutes is proof hydrostatic pressure held on fire hose couplings under IS 903?",
        "expected_tokens": ["2.5 minutes"],
        "expected_standard": "IS 903",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-049",
        "category": "Env - Rubber Gloves Ageing Condition",
        "query": "What accelerated ageing condition is specified for sterile rubber surgical gloves under IS 13422?",
        "expected_tokens": ["ageing", "tensile"],
        "expected_standard": "IS 13422",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 5: Tables & Tolerances (10 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-050",
        "category": "Table - E27 Cap Torsion Limit",
        "query": "What is the mechanical torque limit for E27 lamp caps in Table 2 of IS 16102 (Part 1)?",
        "expected_tokens": ["3.0 Nm"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-051",
        "category": "Table - B22d Cap Torque Limit",
        "query": "What is the torque limit for B22d lamp caps in Table 2 of IS 16102 (Part 1)?",
        "expected_tokens": ["3.0 Nm"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-052",
        "category": "Table - E14 Cap Torque Limit",
        "query": "What is the mechanical torque limit for E14 lamp caps in Table 2 of IS 16102 (Part 1)?",
        "expected_tokens": ["1.15 Nm"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-053",
        "category": "Table - E17 Cap Torque Limit",
        "query": "What torque limit applies to E17 lamp caps in Table 2 of IS 16102 (Part 1)?",
        "expected_tokens": ["1.5 Nm"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-054",
        "category": "Table - GX53 Cap Torque Status",
        "query": "What is the torque requirement for GX53 caps in Table 2 of IS 16102 (Part 1):2012?",
        "as_of_date": "2018-01-01",
        "expected_tokens": ["3.0 Nm", "under consideration"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-055",
        "category": "Table - Fe 500 vs Fe 500D Tensile Ratio",
        "query": "What is the minimum tensile strength to yield stress ratio for Fe 500D steel bars in IS 1786 Table 3?",
        "expected_tokens": ["1.10"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-056",
        "category": "Table - Fe 500D Chemical Carbon Limit",
        "query": "What is the maximum carbon percentage for Fe 500D steel bars in Table 1 of IS 1786?",
        "expected_tokens": ["0.25%"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-057",
        "category": "Table - Fe 500D Max Sulfur Limit",
        "query": "What is the maximum sulfur limit for Fe 500D grade rebar in Table 1 of IS 1786?",
        "expected_tokens": ["0.040%"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-058",
        "category": "Table - Fe 500D Phosphorus Limit",
        "query": "What is the maximum phosphorus limit for Fe 500D steel rebar in Table 1 of IS 1786?",
        "expected_tokens": ["0.040%"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-059",
        "category": "Table - Domestic Water Meter Accuracy Classes",
        "query": "What are the maximum permissible errors in upper and lower flow zones for Class A and B water meters in IS 779?",
        "expected_tokens": ["±2%", "±5%"],
        "expected_standard": "IS 779",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 6: Clauses & Hierarchy (10 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-060",
        "category": "Clause - LED Lamp Marking",
        "query": "Which clause in IS 16102 (Part 1) specifies marking requirements for self-ballasted LED lamps?",
        "expected_tokens": ["Clause 5", "Marking"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-061",
        "category": "Clause - LED Lamp Insulation Resistance",
        "query": "Which clause in IS 16102 (Part 1) governs insulation resistance and electric strength?",
        "expected_tokens": ["Clause 8"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-062",
        "category": "Clause - LED Lamp Cap Mechanical Strength",
        "query": "Which clause in IS 16102 (Part 1) covers mechanical strength and torsion resistance of lamp caps?",
        "expected_tokens": ["Clause 9"],
        "expected_standard": "IS 16102 (Part 1)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-063",
        "category": "Clause - Rebar Chemical Composition",
        "query": "Which clause in IS 1786 specifies chemical composition requirements for deformed steel bars?",
        "expected_tokens": ["Clause 4"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-064",
        "category": "Clause - Rebar Mechanical Properties",
        "query": "Which clause in IS 1786 specifies mechanical properties such as yield stress and tensile strength?",
        "expected_tokens": ["Clause 7"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-065",
        "category": "Clause - Cement Physical Properties",
        "query": "Which clause in IS 269 specifies physical requirements such as fineness and compressive strength of 53 grade cement?",
        "expected_tokens": ["Clause 6"],
        "expected_standard": "IS 269",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-066",
        "category": "Clause - Drinking Water Microbiological Requirements",
        "query": "Which clause in IS 14543 specifies microbiological requirements for packaged drinking water?",
        "expected_tokens": ["Clause 5"],
        "expected_standard": "IS 14543",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-067",
        "category": "Clause - Helmet Shock Absorption Test",
        "query": "Which clause in IS 4151 describes the shock absorption test for protective helmets?",
        "expected_tokens": ["Clause 8", "Shock"],
        "expected_standard": "IS 4151",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-068",
        "category": "Clause - Safety Footwear Basic Requirements",
        "query": "Which clause in IS 15298 (Part 2) covers basic requirements for safety footwear?",
        "expected_tokens": ["Clause 5"],
        "expected_standard": "IS 15298 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-069",
        "category": "Clause - Medical Mask Bacterial Filtration",
        "query": "Which clause in IS 16289 covers performance requirements for bacterial filtration efficiency?",
        "expected_tokens": ["Clause 5"],
        "expected_standard": "IS 16289",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 7: Revision & Edition Differences (10 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-070",
        "category": "Revision - Rebar Agt Mandatory in 2024",
        "query": "What total elongation at maximum force (Agt) requirement was made mandatory in IS 1786 : 2024 for Fe 500D?",
        "expected_tokens": ["Agt ≥ 5.0%"],
        "expected_standard": "IS 1786 : 2024",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-071",
        "category": "Revision - Rebar Fe 700 Grade Addition",
        "query": "Which high strength grade Fe 700 was introduced in the latest revision of IS 1786 : 2024?",
        "expected_tokens": ["Fe 700", "700 MPa"],
        "expected_standard": "IS 1786 : 2024",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-072",
        "category": "Revision - Ceiling Fan BLDC in 2026",
        "query": "What motor technology provisions were incorporated into IS 374 : 2026 for electric ceiling fans?",
        "expected_tokens": ["BLDC", "brushless"],
        "expected_standard": "IS 374 : 2026",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-073",
        "category": "Revision - Ceiling Fan Star Rating Harmonization",
        "query": "What energy efficiency service value harmonization is specified in IS 374 : 2026?",
        "expected_tokens": ["BEE", "star rating"],
        "expected_standard": "IS 374 : 2026",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-074",
        "category": "Revision - LED Lamp Photobiological Safety in 2026",
        "query": "What photobiological safety requirement according to IS 16108 was added in IS 16102 (Part 1) : 2026?",
        "expected_tokens": ["photobiological safety", "blue light"],
        "expected_standard": "IS 16102 (Part 1) : 2026",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-075",
        "category": "Revision - LED Lamp GX53 Cap Solidified",
        "query": "What happened to the GX53 cap torque requirement in IS 16102 (Part 1) : 2026 compared to 2012?",
        "expected_tokens": ["3.0 Nm"],
        "expected_standard": "IS 16102 (Part 1) : 2026",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-076",
        "category": "Revision - Rebar 2008 Edition Fe 500D Properties",
        "query": "What were the specified properties of Fe 500D in IS 1786 : 2008 before the 2024 revision?",
        "as_of_date": "2015-01-01",
        "expected_tokens": ["500.0 MPa", "16.0%"],
        "expected_standard": "IS 1786 : 2008",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-077",
        "category": "Revision - Cement Standard Consolidation",
        "query": "What happened to IS 8112 (43 Grade) and IS 12269 (53 Grade) in the 2015 revision of IS 269?",
        "expected_tokens": ["IS 269", "53 Grade"],
        "expected_standard": "IS 269",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-078",
        "category": "Revision - LED Performance Life Claim in 2017",
        "query": "What rated life requirement is specified in IS 16102 (Part 2) : 2017 for LED lamps?",
        "expected_tokens": ["25 000 h"],
        "expected_standard": "IS 16102 (Part 2) : 2017",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-079",
        "category": "Revision - Pressure Cooker 5th Revision Burst Pressure",
        "query": "What is the burst pressure requirement in IS 2347 : 2017 Fifth Revision?",
        "expected_tokens": ["3.0 bar"],
        "expected_standard": "IS 2347 : 2017",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 8: Temporal Effective Dates & Versioning (10 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-080",
        "category": "Temporal - IS 1786 Effective in 2015",
        "query": "Which version of IS 1786 was in force on 2015-06-01?",
        "as_of_date": "2015-06-01",
        "expected_tokens": ["IS 1786 : 2008"],
        "expected_standard": "IS 1786 : 2008",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-081",
        "category": "Temporal - IS 1786 Effective in 2025",
        "query": "Which version of IS 1786 is in force on 2025-01-01?",
        "as_of_date": "2025-01-01",
        "expected_tokens": ["IS 1786 : 2024"],
        "expected_standard": "IS 1786 : 2024",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-082",
        "category": "Temporal - IS 374 Effective in 2020",
        "query": "Which edition of IS 374 was in force in 2020?",
        "as_of_date": "2020-01-01",
        "expected_tokens": ["IS 374 : 2019"],
        "expected_standard": "IS 374 : 2019",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-083",
        "category": "Temporal - IS 374 Effective in 2027",
        "query": "Which edition of IS 374 is active in 2027?",
        "as_of_date": "2027-01-01",
        "expected_tokens": ["IS 374 : 2026"],
        "expected_standard": "IS 374 : 2026",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-084",
        "category": "Temporal - LED Lamp Part 1 Active in 2018",
        "query": "What edition of IS 16102 (Part 1) applied in 2018?",
        "as_of_date": "2018-01-01",
        "expected_tokens": ["IS 16102 (Part 1) : 2012"],
        "expected_standard": "IS 16102 (Part 1) : 2012",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-085",
        "category": "Temporal - LED Lamp Part 1 Active in 2027",
        "query": "What edition of IS 16102 (Part 1) is active in 2027?",
        "as_of_date": "2027-01-01",
        "expected_tokens": ["IS 16102 (Part 1) : 2026"],
        "expected_standard": "IS 16102 (Part 1) : 2026",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-086",
        "category": "Temporal - LED Lamp Part 2 Active in 2015",
        "query": "Which edition of IS 16102 (Part 2) applied on 2015-01-01?",
        "as_of_date": "2015-01-01",
        "expected_tokens": ["IS 16102 (Part 2)"],
        "expected_standard": "IS 16102 (Part 2)",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-087",
        "category": "Temporal - Packaged Water Active Edition",
        "query": "What is the current third revision edition of IS 14543 for packaged drinking water?",
        "expected_tokens": ["IS 14543 : 2024"],
        "expected_standard": "IS 14543 : 2024",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-088",
        "category": "Temporal - Concrete Aggregate 2016 Revision",
        "query": "What edition of IS 383 covers coarse and fine aggregates for concrete?",
        "expected_tokens": ["IS 383 : 2016"],
        "expected_standard": "IS 383 : 2016",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-089",
        "category": "Temporal - Structural Steel Active Edition",
        "query": "What revision of IS 2062 is currently in force for hot rolled medium and high tensile structural steel?",
        "expected_tokens": ["IS 2062 : 2011"],
        "expected_standard": "IS 2062 : 2011",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 9: QCOs & Gazette Notifications (5 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-090",
        "category": "QCO - Compulsory Registration Scheme",
        "query": "What order establishes the Compulsory Registration Scheme (CRS) for electronic goods?",
        "expected_tokens": ["CRO", "Compulsory Registration"],
        "expected_standard": "CRO",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-091",
        "category": "QCO - CRO Amendment 2026",
        "query": "What are the key provisions of the CRO Amendment 2026?",
        "expected_tokens": ["CRO Amendment", "2026"],
        "expected_standard": "CRO",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-092",
        "category": "QCO - Mandatory Mark for Helmets",
        "query": "Under Quality Control Orders, what certification mark is mandatory for motorcycle helmets?",
        "expected_tokens": ["ISI Mark", "Standard Mark"],
        "expected_standard": "IS 4151",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-093",
        "category": "QCO - Mandatory Registration for LED Lamps",
        "query": "Which regulatory scheme mandates registration for self-ballasted LED lamps?",
        "expected_tokens": ["CRS", "Registration"],
        "expected_standard": "IS 16102",
        "must_pass_guardrail": True,
        "is_refusal": False
    },
    {
        "id": "RAG-094",
        "category": "QCO - Steel QCO Compliance",
        "query": "Under the Steel and Steel Products Quality Control Order, which standard applies to TMT rebar?",
        "expected_tokens": ["IS 1786"],
        "expected_standard": "IS 1786",
        "must_pass_guardrail": True,
        "is_refusal": False
    },

    # -------------------------------------------------------------------------
    # Category 10: Adversarial / Hallucination Resistance & Refusals (11 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "RAG-095",
        "category": "Adversarial - Rocket Engine Refusal",
        "query": "What is the BIS requirement for rocket engines and thrusters?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-096",
        "category": "Adversarial - Commercial Price Refusal",
        "query": "What is the retail price of an IS 374 compliant ceiling fan in the Indian market?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-097",
        "category": "Adversarial - Non-Existent Fake Standard IS 99999",
        "query": "According to IS 99999 : 2025, what is the maximum permissible sulfur content?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-098",
        "category": "Adversarial - Non-Existent Grade Fe 9999",
        "query": "Under IS 1786 : 2024, what is the minimum yield stress for Grade Fe 9999?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-099",
        "category": "Adversarial - Outside Scope Recipe Query",
        "query": "Give me a recipe for chocolate cake according to Indian Standards.",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-100",
        "category": "Adversarial - Quantum Computer BIS Norms",
        "query": "What are the BIS testing standards for quantum computers with 1000 qubits?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-101",
        "category": "Adversarial - Stock Market Trading Tips",
        "query": "Which stock should I buy to benefit from the BIS QCO on steel?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-102",
        "category": "Adversarial - Spacecraft Heat Shield Norms",
        "query": "What is the thermal conductivity limit for spacecraft heat shields under BIS regulations?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-103",
        "category": "Adversarial - Fake Cap Type Z99",
        "query": "What is the mechanical torque requirement for lamp cap Z99 in IS 16102 (Part 1)?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-104",
        "category": "Adversarial - Weather Forecast Query",
        "query": "What is the weather forecast for New Delhi according to BIS meteorological norms?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    },
    {
        "id": "RAG-105",
        "category": "Adversarial - Cryptocurrency Legal Status",
        "query": "What is the BIS licensing scheme for Bitcoin mining hardware?",
        "expected_tokens": ["could not find sufficient"],
        "expected_standard": None,
        "must_pass_guardrail": True,
        "is_refusal": True
    }
]


def run_benchmark():
    pipeline = RAGPipeline()
    print("=" * 115)
    print("🎯 BIS AI ASSISTANT - PHASE 2F EXTENDED 105-QUESTION RAG BENCHMARK EVALUATION")
    print("=" * 115)
    print(f"{'ID':<9} | {'Category':<32} | {'Grounding':<10} | {'Citations':<10} | {'Guardrail':<10} | {'Status'}")
    print("-" * 115)

    passed_count = 0
    total = len(BENCHMARK_CASES)

    for case in BENCHMARK_CASES:
        ans = pipeline.answer_question(
            query=case["query"],
            as_of_date=case.get("as_of_date")
        )
        
        # Check token presence
        grounding_pass = all(tok.lower() in ans.answer.lower() for tok in case["expected_tokens"])
        
        # Check citations
        if case["is_refusal"]:
            citations_pass = True
        else:
            citations_pass = len(ans.citations) > 0 and any(c.verified for c in ans.citations)
            if case["expected_standard"]:
                citations_pass = citations_pass and any(case["expected_standard"].lower() in c.standard_number.lower() for c in ans.citations)

        guardrail_pass = ans.guardrail_result.passed

        case_success = grounding_pass and citations_pass and guardrail_pass
        if case_success:
            passed_count += 1

        status_str = "✅ PASS" if case_success else "❌ FAIL"
        print(
            f"{case['id']:<9} | {case['category']:<32} | "
            f"{('✅' if grounding_pass else '❌'):<10} | "
            f"{('✅' if citations_pass else '❌'):<10} | "
            f"{('✅' if guardrail_pass else '❌'):<10} | "
            f"{status_str}"
        )

    print("=" * 115)
    acc = (passed_count / total) * 100
    print(f"📊 BENCHMARK SUMMARY: {passed_count}/{total} PASSED ({acc:.1f}% Accuracy)")
    print("=" * 115)

    if acc < 100.0:
        sys.exit(1)


if __name__ == "__main__":
    run_benchmark()
