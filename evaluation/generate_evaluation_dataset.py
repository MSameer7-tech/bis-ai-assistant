"""
Dataset Generator for 25-Product Multi-Dimensional RAG Evaluation.
Produces data/evaluation/rag_25_product_test_cases.json with 400+ deterministic test cases.
"""
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "data" / "ps_coverage" / "ps_products.json"
OUTPUT_DATASET = ROOT_DIR / "data" / "evaluation" / "rag_25_product_test_cases.json"


def generate_dataset():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    products = manifest.get("products", [])
    test_cases = []
    
    # 1. Per-Product Category Test Cases (25 products x 14-16 question types = 375+ cases)
    for p in products:
        pid = p["id"]
        cname = p["canonical_name"]
        std = p["canonical_standard"]
        scheme = p["scheme"]
        is_mand = p["mandatory_certification"]
        aliases = p.get("aliases", [])
        primary_alias = aliases[0] if aliases else cname.lower()
        secondary_alias = aliases[1] if len(aliases) > 1 else primary_alias

        # A. Standard Identification
        test_cases.append({
            "case_id": f"{pid}-STD-01",
            "product_id": pid,
            "product_name": cname,
            "category": "standard_identification",
            "question": f"What Indian Standard applies to {primary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["standard_identity"],
            "must_contain": [std],
            "should_refuse": False
        })
        test_cases.append({
            "case_id": f"{pid}-STD-02",
            "product_id": pid,
            "product_name": cname,
            "category": "standard_identification",
            "question": f"Which BIS standard number specifies requirements for {cname}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["standard_identity"],
            "must_contain": [std],
            "should_refuse": False
        })

        # B. Natural-Language Manufacturing Query (No IS code mentioned)
        test_cases.append({
            "case_id": f"{pid}-NL-01",
            "product_id": pid,
            "product_name": cname,
            "category": "natural_language_query",
            "question": f"I manufacture {primary_alias}. Which BIS standard applies to my manufacturing unit?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["standard_identity", "mandatory_status"],
            "must_contain": [std],
            "should_refuse": False
        })

        # C. Mandatory Certification
        test_cases.append({
            "case_id": f"{pid}-MAND-01",
            "product_id": pid,
            "product_name": cname,
            "category": "mandatory_certification",
            "question": f"Is BIS certification mandatory for {primary_alias} in India?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["mandatory_status"],
            "must_contain": ["Mandatory" if is_mand else "Voluntary", std],
            "should_refuse": False
        })
        test_cases.append({
            "case_id": f"{pid}-MAND-02",
            "product_id": pid,
            "product_name": cname,
            "category": "mandatory_certification",
            "question": f"Do I need a BIS licence or registration before selling {secondary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["mandatory_status", "scheme"],
            "must_contain": [scheme, std],
            "should_refuse": False
        })

        # D. Quality Control Order (QCO)
        test_cases.append({
            "case_id": f"{pid}-QCO-01",
            "product_id": pid,
            "product_name": cname,
            "category": "qco",
            "question": f"Which Quality Control Order (QCO) makes certification compulsory for {primary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["qco"],
            "must_contain": [std],
            "should_refuse": False
        })

        # E. Certification Scheme
        test_cases.append({
            "case_id": f"{pid}-SCHEME-01",
            "product_id": pid,
            "product_name": cname,
            "category": "certification_scheme",
            "question": f"Which BIS certification scheme governs {cname} (e.g., Scheme I, Scheme II, Scheme IV)?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["scheme"],
            "must_contain": [scheme],
            "should_refuse": False
        })

        # F. Testing Requirements
        test_cases.append({
            "case_id": f"{pid}-TEST-01",
            "product_id": pid,
            "product_name": cname,
            "category": "testing_requirements",
            "question": f"What testing requirements and parameter checks are specified for {primary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["testing_requirements"],
            "must_contain": [std],
            "should_refuse": False
        })

        # G. Product Manual (if Scheme-I, else verify non-applicable/CRS)
        test_cases.append({
            "case_id": f"{pid}-PM-01",
            "product_id": pid,
            "product_name": cname,
            "category": "product_manual",
            "question": f"What guidelines and grouping rules are specified in the Product Manual for {primary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["product_manual"] if scheme == "SCHEME-I" else ["scheme"],
            "must_contain": [std],
            "should_refuse": False
        })

        # H. Scheme of Inspection and Testing (SIT)
        test_cases.append({
            "case_id": f"{pid}-SIT-01",
            "product_id": pid,
            "product_name": cname,
            "category": "sit",
            "question": f"What is the Scheme of Inspection and Testing (SIT) and sampling frequency for {primary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["sit"] if scheme == "SCHEME-I" else ["scheme"],
            "must_contain": [std],
            "should_refuse": False
        })

        # I. Laboratory Lookup
        test_cases.append({
            "case_id": f"{pid}-LAB-01",
            "product_id": pid,
            "product_name": cname,
            "category": "laboratory",
            "question": f"Which BIS recognized laboratories can test {primary_alias} under {std}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["laboratory"],
            "must_contain": [std],
            "should_refuse": False
        })

        # J. Licensing / Procedure
        test_cases.append({
            "case_id": f"{pid}-LIC-01",
            "product_id": pid,
            "product_name": cname,
            "category": "licensing_procedure",
            "question": f"How do I obtain a BIS licence or certificate of conformity for {primary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["licensing", "scheme"],
            "must_contain": [scheme, std],
            "should_refuse": False
        })

        # K. Related Standards & Technical Domain
        test_cases.append({
            "case_id": f"{pid}-REL-01",
            "product_id": pid,
            "product_name": cname,
            "category": "related_standards",
            "question": f"What is the technical department and standard framework governing {cname}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["standard_identity"],
            "must_contain": [std],
            "should_refuse": False
        })

        # L. Amendment & Active Revision Check
        test_cases.append({
            "case_id": f"{pid}-AMD-01",
            "product_id": pid,
            "product_name": cname,
            "category": "amendment_current_version",
            "question": f"What is the current active revision and amendment status of {std} for {primary_alias}?",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["amendment_version"],
            "must_contain": [std],
            "should_refuse": False
        })

        # M. Multi-Part Comprehensive Query
        test_cases.append({
            "case_id": f"{pid}-MULTI-01",
            "product_id": pid,
            "product_name": cname,
            "category": "multi_part_query",
            "question": f"I manufacture {primary_alias}. Tell me the applicable BIS standard, whether certification is mandatory, the certification scheme, and what tests are required.",
            "expected_product_id": pid,
            "expected_standard": std,
            "expected_scheme": scheme,
            "expected_mandatory": is_mand,
            "expected_information_types": ["standard_identity", "mandatory_status", "scheme", "testing_requirements"],
            "must_contain": [std, scheme],
            "should_refuse": False
        })

        # N. Alias / Plural / Singular / Industrial Variant Query
        if len(aliases) >= 2:
            test_cases.append({
                "case_id": f"{pid}-ALIAS-01",
                "product_id": pid,
                "product_name": cname,
                "category": "alias_variation",
                "question": f"What BIS regulatory requirements apply to {aliases[-1]}?",
                "expected_product_id": pid,
                "expected_standard": std,
                "expected_scheme": scheme,
                "expected_mandatory": is_mand,
                "expected_information_types": ["standard_identity"],
                "must_contain": [std],
                "should_refuse": False
            })

    # 2. Cross-Product Confusion Queries (10 test cases)
    cross_product_pairs = [
        ("PS-002", "TMT steel reinforcement bars", "PS-007", "cement", "I manufacture TMT steel reinforcement bars for concrete. Which BIS standard applies to my steel rebars?"),
        ("PS-007", "Ordinary Portland Cement", "PS-002", "TMT steel", "What standard applies to OPC 53 grade cement used with rebar?"),
        ("PS-001", "Electric Ceiling Fans", "PS-006", "LED lamps", "I make 5-star electric ceiling fans with BLDC motor. What BIS standard applies?"),
        ("PS-006", "Self-Ballasted LED Lamps", "PS-001", "ceiling fans", "What BIS certification applies to self-ballasted LED lamps and retrofit bulbs?"),
        ("PS-003", "Lithium-Ion Batteries", "PS-015", "Laptops", "Which BIS standard covers lithium-ion secondary cells and battery packs?"),
        ("PS-015", "Laptops & Notebook Computers", "PS-016", "Smartphones", "Which standard applies to laptop and notebook computer hardware?"),
        ("PS-004", "Gold Jewellery", "PS-005", "Silver Jewellery", "What is the mandatory hallmarking standard for 22k gold jewellery?"),
        ("PS-005", "Silver Jewellery", "PS-004", "Gold Jewellery", "What is the mandatory hallmarking standard for 925 sterling silver jewellery?"),
        ("PS-010", "Domestic Gas Stoves", "PS-011", "Pressure Cookers", "Which BIS standard applies to domestic LPG gas stoves?"),
        ("PS-011", "Domestic Pressure Cookers", "PS-010", "Gas Stoves", "Which BIS standard applies to domestic pressure cookers?")
    ]
    for idx, (target_pid, target_name, conf_pid, conf_name, q) in enumerate(cross_product_pairs, 1):
        target_prod = next(p for p in products if p["id"] == target_pid)
        test_cases.append({
            "case_id": f"CONFUSION-{idx:02d}",
            "product_id": target_pid,
            "product_name": target_prod["canonical_name"],
            "category": "cross_product_confusion",
            "question": q,
            "expected_product_id": target_pid,
            "expected_standard": target_prod["canonical_standard"],
            "expected_scheme": target_prod["scheme"],
            "expected_mandatory": target_prod["mandatory_certification"],
            "expected_information_types": ["standard_identity"],
            "must_contain": [target_prod["canonical_standard"]],
            "should_refuse": False,
            "confusion_risk_with": conf_pid
        })

    # 3. Negative / Adversarial / Out-of-Scope Queries (20 test cases)
    negative_queries = [
        ("NEG-01", "What is the BIS standard for titanium quantum processors?", "titanium quantum processors"),
        ("NEG-02", "What is the BIS certification requirement for teleportation devices?", "teleportation devices"),
        ("NEG-03", "Does BIS certify fictional anti-gravity propulsion engines?", "fictional propulsion engines"),
        ("NEG-04", "What is the capital of France?", "general knowledge out of scope"),
        ("NEG-05", "What is the tensile strength of graphene superconductors under BIS?", "graphene superconductors"),
        ("NEG-06", "Which Indian Standard covers commercial starships and warp drives?", "starships"),
        ("NEG-07", "What is the BIS licence requirement for carbon nanotube space elevators?", "space elevators"),
        ("NEG-08", "How do I get an ISI mark for dark matter containment units?", "dark matter containment"),
        ("NEG-09", "What is the mandatory QCO for holographic quantum computers?", "holographic quantum computers"),
        ("NEG-10", "Which BIS standard governs lightsabers and plasma blasters?", "fictional weapons"),
        ("NEG-11", "What is the recipe for chocolate cake?", "unrelated cooking recipe"),
        ("NEG-12", "What is the GDP of India in 2026?", "unrelated economic question"),
        ("NEG-13", "Who won the FIFA world cup in 2022?", "unrelated sports query"),
        ("NEG-14", "What BIS standard applies to titanium water bottles?", "titanium water bottles"),
        ("NEG-15", "Is BIS certification required for synthetic vibranium alloy plates?", "fictional vibranium"),
        ("NEG-16", "What are the test requirements for laser cannons under BIS?", "laser cannons"),
        ("NEG-17", "How to write a binary search algorithm in Python?", "programming tutorial query"),
        ("NEG-18", "What is the airspeed velocity of an unladen swallow?", "fictional trivia"),
        ("NEG-19", "Which BIS standard covers adamantium surgical implants?", "fictional material"),
        ("NEG-20", "What BIS certification is required for cold fusion reactors?", "cold fusion reactors")
    ]
    for cid, q, topic in negative_queries:
        test_cases.append({
            "case_id": cid,
            "product_id": None,
            "product_name": None,
            "category": "negative_out_of_scope",
            "question": q,
            "expected_product_id": None,
            "expected_standard": None,
            "expected_scheme": None,
            "expected_mandatory": None,
            "expected_information_types": [],
            "must_contain": [],
            "should_refuse": True,
            "out_of_scope_topic": topic
        })

    # 4. Ambiguous Queries (10 test cases)
    ambiguous_queries = [
        ("AMB-01", "What is the BIS standard for steel?", "Multiple steel standards (IS 1786, IS 2062, IS 432)"),
        ("AMB-02", "What BIS certification do I need for electrical equipment?", "Multiple electrical product categories"),
        ("AMB-03", "Which standard applies to a fan?", "Could refer to ceiling, table, pedestal, or industrial fan"),
        ("AMB-04", "Is BIS certification mandatory for cables?", "Could refer to PVC cables IS 694 or power cables IS 7098"),
        ("AMB-05", "What is the test requirement for cement?", "Could refer to OPC IS 269 or PPC IS 1489"),
        ("AMB-06", "What are the rules for pipes in India?", "Could refer to UPVC pipes IS 4985 or HDPE pipes IS 4984"),
        ("AMB-07", "How to get a licence for kitchen appliances?", "Multiple distinct kitchen appliance standards"),
        ("AMB-08", "What standard applies to water?", "Could refer to Packaged Drinking Water IS 14543 or Natural Mineral Water IS 13428"),
        ("AMB-09", "Is hallmarking compulsory for jewellery?", "Applies to Gold IS 1417 and Silver IS 2112"),
        ("AMB-10", "What BIS scheme covers electronics?", "Scheme-II CRS covers most IT & AV goods")
    ]
    for cid, q, ambig_desc in ambiguous_queries:
        test_cases.append({
            "case_id": cid,
            "product_id": None,
            "product_name": None,
            "category": "ambiguous_query",
            "question": q,
            "expected_product_id": None,
            "expected_standard": None,
            "expected_scheme": None,
            "expected_mandatory": None,
            "expected_information_types": [],
            "must_contain": [],
            "should_refuse": False,
            "ambiguity_description": ambig_desc
        })

    # 5. Multi-Turn Conversational Suites (5 suites x 4 turns = 20 test cases)
    conversational_suites = [
        {
            "suite_id": "CONV-01",
            "product_id": "PS-001",
            "product_name": "Electric Ceiling Fans",
            "turns": [
                ("CONV-01-T1", "I manufacture electric ceiling fans.", "standard_identification", ["IS 374"]),
                ("CONV-01-T2", "Is BIS certification mandatory for my product?", "mandatory_certification", ["Mandatory", "IS 374"]),
                ("CONV-01-T3", "Which tests are required?", "testing_requirements", ["IS 374"]),
                ("CONV-01-T4", "Which laboratories can perform those tests?", "laboratory", ["IS 374"])
            ]
        },
        {
            "suite_id": "CONV-02",
            "product_id": "PS-002",
            "product_name": "TMT Steel Reinforcement Bars",
            "turns": [
                ("CONV-02-T1", "I manufacture TMT steel reinforcement bars.", "standard_identification", ["IS 1786"]),
                ("CONV-02-T2", "Is BIS certification mandatory?", "mandatory_certification", ["Mandatory", "IS 1786"]),
                ("CONV-02-T3", "What tests must I conduct in the factory under SIT?", "sit", ["IS 1786"]),
                ("CONV-02-T4", "How do I apply for the CM/L licence?", "licensing_procedure", ["SCHEME-I"])
            ]
        },
        {
            "suite_id": "CONV-03",
            "product_id": "PS-003",
            "product_name": "Lithium-Ion Secondary Batteries & Cells",
            "turns": [
                ("CONV-03-T1", "I import lithium-ion secondary batteries for electronics.", "standard_identification", ["IS 16046"]),
                ("CONV-03-T2", "Which scheme applies to battery registration?", "certification_scheme", ["SCHEME-II"]),
                ("CONV-03-T3", "What safety tests are mandatory?", "testing_requirements", ["IS 16046"]),
                ("CONV-03-T4", "Which labs are recognized for testing?", "laboratory", ["IS 16046"])
            ]
        },
        {
            "suite_id": "CONV-04",
            "product_id": "PS-004",
            "product_name": "Gold Jewellery & Gold Bullion (Hallmarking)",
            "turns": [
                ("CONV-04-T1", "I am a jeweller selling 22k gold jewellery in India.", "standard_identification", ["IS 1417"]),
                ("CONV-04-T2", "Is 6-digit HUID hallmarking compulsory?", "mandatory_certification", ["Mandatory", "IS 1417"]),
                ("CONV-04-T3", "What certification scheme covers gold hallmarking?", "certification_scheme", ["SCHEME-IV"]),
                ("CONV-04-T4", "Where can I find recognized Assaying & Hallmarking Centres?", "laboratory", ["IS 1417"])
            ]
        },
        {
            "suite_id": "CONV-05",
            "product_id": "PS-007",
            "product_name": "Ordinary Portland Cement (33, 43, 53 Grades)",
            "turns": [
                ("CONV-05-T1", "We produce 53 grade Ordinary Portland Cement.", "standard_identification", ["IS 269"]),
                ("CONV-05-T2", "Do we need an ISI mark licence before dispatch?", "mandatory_certification", ["Mandatory", "IS 269"]),
                ("CONV-05-T3", "What are the 28-day compressive strength limits and tests?", "testing_requirements", ["IS 269"]),
                ("CONV-05-T4", "What does the Product Manual specify for lot sampling?", "product_manual", ["IS 269"])
            ]
        }
    ]

    for s in conversational_suites:
        pid = s["product_id"]
        prod = next(p for p in products if p["id"] == pid)
        for tid, q, cat, must_c in s["turns"]:
            test_cases.append({
                "case_id": tid,
                "suite_id": s["suite_id"],
                "product_id": pid,
                "product_name": s["product_name"],
                "category": f"multi_turn_{cat}",
                "question": q,
                "expected_product_id": pid,
                "expected_standard": prod["canonical_standard"],
                "expected_scheme": prod["scheme"],
                "expected_mandatory": prod["mandatory_certification"],
                "expected_information_types": [cat],
                "must_contain": must_c,
                "should_refuse": False
            })

    dataset = {
        "manifest_version": "1.0",
        "description": "Comprehensive 25-Product Multi-Dimensional RAG Evaluation Dataset",
        "total_test_cases": len(test_cases),
        "total_products_covered": len(products),
        "test_cases": test_cases
    }

    OUTPUT_DATASET.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DATASET, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated Evaluation Dataset: {len(test_cases)} test cases written to {OUTPUT_DATASET}")
    return dataset


if __name__ == "__main__":
    generate_dataset()
