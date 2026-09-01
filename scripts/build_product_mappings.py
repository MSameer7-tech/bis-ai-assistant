#!/usr/bin/env python3
"""
Dynamic Product Registry & Terminology Generator (Stage 8/9).
Extracts natural language product phrases, colloquial synonyms, domain descriptors,
and titles from the 550-entity BIS catalog into data/registry/products.jsonl.
Every entry includes confidence, evidence source, and local document availability.
"""
import os
import sys
import json
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REGISTRY_DIR = DATA_DIR / "registry"

# Known local available documents
LOCAL_STANDARDS_DIR = DATA_DIR / "raw" / "standards"


def is_document_locally_available(standard_number: str) -> bool:
    """Checks if the document is available in local data/raw/standards."""
    if not LOCAL_STANDARDS_DIR.exists():
        return False
    clean_num = standard_number.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
    matches = list(LOCAL_STANDARDS_DIR.glob(f"*{clean_num}*.pdf"))
    return len(matches) > 0


# Extensive product terminology seed map (Product terms -> Standard Numbers)
PRODUCT_TERMINOLOGY_MAP = [
    # 1. Electrical & Appliances
    {"terms": ["ceiling fan", "ceiling fans", "electric ceiling fan", "bldc fan", "bldc ceiling fan", "energy efficient fan"], "standard": "IS 374", "name": "Electric Ceiling Fans"},
    {"terms": ["table fan", "table fans", "desk fan", "table type electric fans and regulators"], "standard": "IS 555", "name": "Table Type Electric Fans"},
    {"terms": ["exhaust fan", "exhaust fans", "ventilating fan", "propeller type ac ventilating fans"], "standard": "IS 2312", "name": "Propeller Type AC Ventilating and Exhaust Fans"},
    {"terms": ["electrical safety", "household appliances", "general safety household appliances", "domestic appliances"], "standard": "IS 302 (Part 1)", "name": "Safety of Household Electrical Appliances - General"},
    {"terms": ["electric iron", "electric irons", "dry iron", "steam iron"], "standard": "IS 366", "name": "Electric Irons"},
    {"terms": ["water heater", "geyser", "electric water heater", "stationary storage water heater"], "standard": "IS 2082", "name": "Stationary Storage Type Electric Water Heaters"},
    {"terms": ["immersion heater", "water immersion heater", "electric immersion heater"], "standard": "IS 368", "name": "Electric Immersion Water Heaters"},
    {"terms": ["pvc wire", "pvc insulated cable", "domestic wiring", "building wire", "pvc cables"], "standard": "IS 694", "name": "PVC Insulated Cables for Working Voltages up to 1100V"},
    {"terms": ["xlpe cable", "cross linked polyethylene cable", "power cable xlpe"], "standard": "IS 7098 (Part 1)", "name": "Crosslinked Polyethylene Insulated Cables for Voltages up to 1100V"},
    {"terms": ["acsr conductor", "overhead conductor", "aluminum conductor", "transmission wire"], "standard": "IS 398 (Part 2)", "name": "Aluminium Conductors for Overhead Transmission (ACSR)"},
    {"terms": ["light switch", "domestic switch", "modular switch", "switches for domestic installations"], "standard": "IS 3854", "name": "Switches for Domestic and Similar Fixed Electrical Installations"},
    {"terms": ["plug and socket", "3 pin plug", "power socket", "plugs and socket outlets"], "standard": "IS 1293", "name": "Plugs and Socket-Outlets for Domestic and Similar Purposes"},
    {"terms": ["electrical conduit", "steel conduit", "metal conduit for electrical wiring"], "standard": "IS 1653", "name": "Rigid Steel Conduits for Electrical Wiring"},
    {"terms": ["rccb", "elcb", "residual current circuit breaker", "earth leakage circuit breaker"], "standard": "IS 12640 (Part 1)", "name": "Residual Current Operated Circuit-Breakers without Integral Overcurrent Protection (RCCB)"},
    {"terms": ["electric kettle", "kettle", "tea maker"], "standard": "IS 302 (Part 2/Sec 15)", "name": "Electric Kettles and Liquid Heaters"},
    {"terms": ["air conditioner", "room ac", "split ac", "window ac"], "standard": "IS 1391 (Part 1)", "name": "Room Air Conditioners"},
    {"terms": ["refrigerator", "frost free refrigerator", "direct cool fridge"], "standard": "IS 15750", "name": "Frost-Free Refrigerating Appliances"},

    # 2. Electronics, IT & Lighting
    {"terms": ["led bulb", "led bulbs", "self ballasted led lamp", "self ballasted led lamps", "self-ballasted led lamp", "self-ballasted led lamps", "led lamp", "led lamps", "led light bulb", "b22 led bulb", "e27 led bulb"], "standard": "IS 16102 (Part 1)", "name": "Self-Ballasted LED Lamps for General Lighting — Safety"},
    {"terms": ["led bulb performance", "led luminous flux", "led efficacy", "led lamp performance", "performance requirements for self ballasted led lamps", "performance of self-ballasted led lamps"], "standard": "IS 16102 (Part 2)", "name": "Self-Ballasted LED Lamps for General Lighting — Performance"},
    {"terms": ["led luminaire", "fixed led luminaire", "led batten", "led downlight", "led panel light"], "standard": "IS 10322 (Part 5/Sec 1)", "name": "Luminaires — Particular Requirements: Fixed General Purpose Luminaires"},
    {"terms": ["led driver", "electronic controlgear for led", "led power supply"], "standard": "IS 15885 (Part 2/Sec 13)", "name": "Lamp Controlgear — AC/DC Supplied Electronic Controlgear for LED Modules"},
    {"terms": ["lithium ion battery", "lithium ion batteries", "lithium-ion battery", "lithium-ion batteries", "li-ion battery", "li ion battery", "lithium battery", "lithium batteries", "secondary lithium battery", "secondary lithium batteries", "secondary lithium cell", "secondary lithium cells", "secondary lithium", "mobile phone battery", "laptop battery", "power bank battery", "lithium pouch cell", "18650 cell"], "standard": "IS 16046 (Part 2)", "name": "Secondary Cells and Batteries Containing Alkaline or Other Non-Acid Electrolytes (Lithium Systems)"},
    {"terms": ["nickel battery", "nickel metal hydride battery", "nimh cell", "nickel cadmium battery"], "standard": "IS 16046 (Part 1)", "name": "Secondary Cells and Batteries Containing Alkaline Electrolytes (Nickel Systems)"},
    {"terms": ["compulsory registration order", "cro", "compulsory registration scheme", "crs", "cro order", "meity cro"], "standard": "IS 13252 (Part 1)", "name": "Compulsory Registration Order (CRO / CRS)"},
    {"terms": ["laptop", "desktop computer", "information technology equipment", "it safety", "computer safety", "server"], "standard": "IS 13252 (Part 1)", "name": "Information Technology Equipment — Safety"},
    {"terms": ["audio video equipment", "television", "smart tv", "amplifier", "music system"], "standard": "IS 616", "name": "Audio, Video and Similar Electronic Apparatus — Safety Requirements"},
    {"terms": ["smart meter", "ac static prepaid electricity meter", "prepaid energy meter"], "standard": "IS 16444 (Part 1)", "name": "AC Static Direct Connected Watt-Hour Smart Meters"},
    {"terms": ["cctv camera", "security camera", "surveillance camera", "ip camera"], "standard": "IS 13252 (Part 1)", "name": "Electronic Security & IT Surveillance Systems"},

    # 3. Steel, Construction & Civil Materials
    {"terms": ["tmt reinforcement bars", "tmt reinforcement bar", "tmt bar", "tmt bars", "high strength deformed steel bars", "reinforcement steel bars", "reinforcement steel", "rebar", "rebars", "concrete reinforcement wire", "fe 500d", "fe 550d", "fe 600"], "standard": "IS 1786", "name": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement"},
    {"terms": ["structural steel", "mild steel plate", "steel section", "structural steel standard", "e250 steel", "e350 steel"], "standard": "IS 2062", "name": "Hot Rolled Medium and High Tensile Structural Steel"},
    {"terms": ["carbon steel billet", "steel billet for re-rolling", "bloom", "slab"], "standard": "IS 2830", "name": "Carbon Steel Cast Billet Ingots, Billets, Blooms and Slabs for Re-rolling"},
    {"terms": ["cold rolled steel sheet", "cr sheet", "cr coil"], "standard": "IS 513 (Part 1)", "name": "Cold Reduced Carbon Steel Sheet and Strip"},
    {"terms": ["hot rolled steel sheet", "hr sheet", "hr plate", "hr coil"], "standard": "IS 1079", "name": "Hot Rolled Carbon Steel Sheet and Strip"},
    {"terms": ["welding electrode", "covered electrode for manual metal arc welding"], "standard": "IS 814", "name": "Covered Electrodes for Manual Metal Arc Welding"},
    {"terms": ["opc cement", "ordinary portland cement", "opc 43", "opc 53", "opc 33"], "standard": "IS 269", "name": "Ordinary Portland Cement (33, 43 and 53 Grades)"},
    {"terms": ["ppc cement", "portland pozzolana cement", "fly ash cement", "pozzolana cement flyash based"], "standard": "IS 1489 (Part 1)", "name": "Portland Pozzolana Cement — Part 1: Fly Ash Based"},
    {"terms": ["calcined clay cement", "ppc calcined clay", "pozzolana cement calcined clay"], "standard": "IS 1489 (Part 2)", "name": "Portland Pozzolana Cement — Part 2: Calcined Clay Based"},
    {"terms": ["portland slag cement", "psc cement", "slag cement"], "standard": "IS 455", "name": "Portland Slag Cement"},
    {"terms": ["plain concrete", "reinforced concrete", "rcc code", "concrete code of practice"], "standard": "IS 456", "name": "Code of Practice for Plain and Reinforced Concrete"},
    {"terms": ["coarse aggregate", "fine aggregate", "concrete aggregate", "sand for concrete", "crushed stone"], "standard": "IS 383", "name": "Coarse and Fine Aggregate for Concrete"},
    {"terms": ["steel structure code", "steel design code", "general construction in steel"], "standard": "IS 800", "name": "General Construction in Steel — Code of Practice"},
    {"terms": ["common burnt clay bricks", "red bricks", "building bricks"], "standard": "IS 1077", "name": "Common Burnt Clay Building Bricks"},
    {"terms": ["concrete block", "hollow concrete block", "solid concrete block"], "standard": "IS 2185 (Part 1)", "name": "Concrete Masonry Units — Hollow and Solid Concrete Blocks"},
    {"terms": ["interlocking concrete paver block", "paver block", "paving block"], "standard": "IS 15658", "name": "Precast Concrete Paving Blocks"},
    {"terms": ["upvc pipe", "pvc water pipe", "potable water supply pipe"], "standard": "IS 4985", "name": "Unplasticized PVC Pipes for Potable Water Supplies"},
    {"terms": ["ceramic tile", "vitrified tile", "floor tile", "wall tile"], "standard": "IS 15622", "name": "Pressed Ceramic Tiles"},
    {"terms": ["tile adhesive", "ceramic tile adhesive", "tile grout"], "standard": "IS 15477", "name": "Adhesives for Use with Ceramic Tiles and Mosaics"},

    # 4. Personal Protective Equipment (PPE) & Automotive Safety
    {"terms": ["industrial safety helmet", "industrial safety helmets", "industrial helmet", "industrial helmets", "hard hat", "hard hats", "safety helmet", "safety helmets", "industrial safety headgear"], "standard": "IS 2925", "name": "Industrial Safety Helmets"},
    {"terms": ["two wheeler helmet", "two wheeler helmets", "motorcycle helmet", "motorcycle helmets", "protective helmet for two wheeler riders", "two wheeler headgear", "rider helmet", "crash helmet", "helmet", "helmets"], "standard": "IS 4151", "name": "Protective Helmets for Two Wheeler Riders"},
    {"terms": ["full body harness", "full body harnesses", "safety harness", "safety harnesses", "safety belt", "safety belts", "fall arrest harness", "fall protection belt", "safety belts and harnesses"], "standard": "IS 3521 (Part 1)", "name": "Personal Protective Equipment — Safety Belts and Harnesses"},
    {"terms": ["safety footwear", "safety shoes", "steel toe boot", "work boots", "protective footwear", "industrial safety shoes"], "standard": "IS 15298 (Part 2)", "name": "Personal Protective Equipment — Part 2: Safety Footwear"},
    {"terms": ["protective gloves", "leather safety gloves", "work gloves", "industrial gloves"], "standard": "IS 6994 (Part 1)", "name": "Industrial Safety Gloves — Leather and Cotton Gloves"},
    {"terms": ["surgical gloves", "medical gloves", "rubber examination gloves"], "standard": "IS 13422", "name": "Surgical Rubber Gloves"},
    {"terms": ["medical face mask", "surgical mask", "3 ply mask"], "standard": "IS 16289", "name": "Medical Face Masks"},
    {"terms": ["respiratory mask", "n95 mask", "particulate filtering respirator", "dust mask"], "standard": "IS 9473", "name": "Respiratory Protective Devices — Filtering Half Masks to Protect Against Particles"},
    {"terms": ["coverall", "ppe coverall", "protective clothing against infectious agents"], "standard": "IS 17423", "name": "Personal Protective Equipment — Protective Coveralls for Healthcare"},

    # 5. Domestic Appliances, Cooking & Gas
    {"terms": ["gas stove", "lpg stove", "gas cookstove", "domestic gas stove", "lpg cookstove", "burner gas stove"], "standard": "IS 4246", "name": "Domestic Gas Stoves for Use with Liquefied Petroleum Gases"},
    {"terms": ["pressure cooker", "domestic pressure cooker", "aluminium pressure cooker", "stainless steel pressure cooker"], "standard": "IS 2347", "name": "Domestic Pressure Cookers"},
    {"terms": ["lpg cylinder", "cooking gas cylinder", "domestic lpg cylinder"], "standard": "IS 3196 (Part 1)", "name": "Welded Low Carbon Steel Cylinders for Low Pressure Liquefiable Gases (LPG)"},
    {"terms": ["lpg regulator", "gas regulator", "low pressure regulator for lpg"], "standard": "IS 9798", "name": "Low Pressure Regulators for Use with Liquefied Petroleum Gas Mixtures"},
    {"terms": ["lpg hose", "gas rubber hose", "rubber hose for lpg"], "standard": "IS 9573", "name": "Rubber Hoses for Liquefied Petroleum Gas (LPG)"},

    # 6. Food, Water & Chemicals
    {"terms": ["bottled drinking water plants", "bottled drinking water plant", "packaged drinking water", "bottled water", "bottled drinking water", "packaged water", "mineral water"], "standard": "IS 14543", "name": "Packaged Drinking Water (Other Than Packaged Natural Mineral Water)"},
    {"terms": ["packaged natural mineral water", "natural mineral water", "spring water"], "standard": "IS 13428", "name": "Packaged Natural Mineral Water"},
    {"terms": ["drinking water", "tap water", "potable water standard", "drinking water specification"], "standard": "IS 10500", "name": "Drinking Water — Specification"},
    {"terms": ["infant milk food", "baby milk", "infant formula"], "standard": "IS 14433", "name": "Infant Milk Substitutes — Specification"},
    {"terms": ["milk powder", "whole milk powder", "skimmed milk powder"], "standard": "IS 1165", "name": "Milk Powder — Specification"},
    {"terms": ["condensed milk", "sweetened condensed milk"], "standard": "IS 1166", "name": "Condensed Milk, Partly Skimmed and Skimmed Condensed Milk"},
    {"terms": ["white butter", "pasteurized butter", "table butter"], "standard": "IS 13690", "name": "Pasteurized Butter — Specification"},
    {"terms": ["edible common salt", "iodized salt", "vacuum evaporated salt", "table salt"], "standard": "IS 7224", "name": "Iodized Salt, Vacuum Evaporated Salt and Refined Iodized Salt"},
    {"terms": ["toilet soap", "bath soap", "grade 1 soap", "grade 2 soap"], "standard": "IS 2888", "name": "Toilet Soap — Specification"},
    {"terms": ["laundry soap", "washing soap", "detergent bar"], "standard": "IS 285", "name": "Laundry Soaps — Specification"},
    {"terms": ["synthetic detergent powder", "washing powder", "laundry detergent"], "standard": "IS 4955", "name": "Synthetic Detergents for Household Use"},

    # 7. Fire Fighting & Mechanical Equipment
    {"terms": ["fire extinguisher", "portable fire extinguisher", "abc fire extinguisher", "co2 fire extinguisher", "dry powder fire extinguisher"], "standard": "IS 15683", "name": "Portable Fire Extinguishers — Performance and Construction"},
    {"terms": ["water fire extinguisher", "foam fire extinguisher"], "standard": "IS 940", "name": "Portable Fire Extinguishers: Water and Foam Type"},
    {"terms": ["fire hose", "delivery hose", "unlined flax fire hose"], "standard": "IS 4927", "name": "Unlined Flax Canvas Hose for Fire Fighting"},
    {"terms": ["fire hydrant", "fire hose delivery coupling", "landing valve"], "standard": "IS 903", "name": "Fire Hose Delivery Couplings, Branch Pipe, Nozzles and Strainer"},
    {"terms": ["water meter", "domestic water meter", "water flow meter"], "standard": "IS 779", "name": "Water Meters (Domestic Type) — Specification"}
]


def build_products_registry():
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Building BIS Product Registry (data/registry/products.jsonl)...")

    # Load catalog entities to cross-reference
    catalog_file = REGISTRY_DIR / "standards_catalog.jsonl"
    catalog_by_std = {}
    if catalog_file.exists():
        with open(catalog_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    if item.get("entity_type") == "standard" and item.get("standard_number"):
                        catalog_by_std[item["standard_number"]] = item

    products: List[Dict[str, Any]] = []
    prod_counter = 1

    seen_pairs = set()

    for p_group in PRODUCT_TERMINOLOGY_MAP:
        std_num = p_group["standard"]
        norm_name = p_group["name"]
        cat_info = catalog_by_std.get(std_num, {})

        edition = cat_info.get("edition", "2024")
        domain = cat_info.get("domain", "general")
        dept = cat_info.get("department", "ETD")
        mandatory = cat_info.get("mandatory_certification", True)
        is_available = is_document_locally_available(std_num)

        for term in p_group["terms"]:
            clean_term = term.strip().lower()
            if (clean_term, std_num) in seen_pairs:
                continue

            # Compute match confidence
            # Exact title match = 1.0, synonym = 0.95-0.98
            confidence = 1.0 if clean_term in norm_name.lower() else 0.95

            prod_record = {
                "product_id": f"PRD-{prod_counter:06d}",
                "term": clean_term,
                "normalized_name": norm_name,
                "standard_number": std_num,
                "current_edition": str(edition),
                "domain": domain,
                "department": dept,
                "mandatory_certification": mandatory,
                "document_available": is_available,
                "confidence": confidence,
                "evidence_source": f"BIS Standards Catalog & Scope ({std_num})",
                "indexed_at": datetime.now().isoformat()
            }
            products.append(prod_record)
            seen_pairs.add((clean_term, std_num))
            prod_counter += 1

    # Also automatically extract product terms from all standards in catalog
    if catalog_file.exists():
        with open(catalog_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("entity_type") != "standard":
                    continue
                
                std_num = item.get("standard_number")
                title = item.get("title", "")
                edition = item.get("edition", "2024")
                domain = item.get("domain", "general")
                dept = item.get("department", "ETD")
                is_available = is_document_locally_available(std_num)

                # Clean title to derive specific product phrase
                EXCLUDE_GENERIC_TERMS = {
                    "personal protective equipment", "medical electrical equipment",
                    "methods of test", "code of practice", "safety requirements",
                    "general requirements", "particular requirements", "luminaires",
                    "lamp controlgear", "information technology equipment",
                    "specification", "specifications", "requirements", "guidelines", "code", "standards",
                    "part", "sampling", "inspection", "testing", "general",
                    "glossary", "terms and definitions", "handbook", "dimensions",
                    "first revision", "second revision", "third revision", "fourth revision", "fifth revision", "sixth revision"
                }

                clean_std_num = re.sub(r"\s*:\s*\d{4}", "", std_num).strip()

                # Extract both specific subtitle (after em-dash/dash) and cleaned full title
                extracted_phrases = []
                if "—" in title or " - " in title or "-" in title:
                    parts = re.split(r"[—\-]", title)
                    for pt in parts:
                        pt_clean = re.sub(r"\(.*?\)", "", pt)
                        pt_clean = re.sub(r"(Specification for|Requirements for|Code of Practice for|Guidelines for|Part \d+.*?:\s*)", "", pt_clean, flags=re.IGNORECASE).strip().lower()
                        if pt_clean and len(pt_clean) > 3 and pt_clean not in EXCLUDE_GENERIC_TERMS:
                            extracted_phrases.append(pt_clean)

                full_clean = re.sub(r"\(.*?\)", "", title)
                full_clean = re.sub(r"(Specification for|Requirements for|Code of Practice for|Guidelines for)", "", full_clean, flags=re.IGNORECASE).strip().lower()
                if full_clean and len(full_clean) > 3 and full_clean not in EXCLUDE_GENERIC_TERMS:
                    extracted_phrases.append(full_clean)

                for phrase in extracted_phrases:
                    if (phrase, clean_std_num) not in seen_pairs:
                        products.append({
                            "product_id": f"PRD-{prod_counter:06d}",
                            "term": phrase,
                            "normalized_name": title,
                            "standard_number": clean_std_num,
                            "current_edition": str(edition),
                            "domain": domain,
                            "department": dept,
                            "mandatory_certification": item.get("mandatory_certification", True),
                            "document_available": is_available,
                            "confidence": 0.90,
                            "evidence_source": f"Derived from BIS Title ({clean_std_num})",
                            "indexed_at": datetime.now().isoformat()
                        })
                        seen_pairs.add((phrase, clean_std_num))
                        prod_counter += 1

    output_file = REGISTRY_DIR / "products.jsonl"
    with open(output_file, "w", encoding="utf-8") as out:
        for p in products:
            out.write(json.dumps(p, ensure_ascii=False) + "\n")

    logger.info(f"✅ Generated {len(products)} product mappings in: {output_file}")
    
    # Print sample
    print("\n" + "=" * 80)
    print("📦 BIS PRODUCT RESOLUTION REGISTRY SUMMARY (STAGE 8)")
    print("=" * 80)
    print(f"Total Product Terms Indexed:  {len(products):>6d}")
    print(f"Unique Standards Mapped:      {len(set(p['standard_number'] for p in products)):>6d}")
    print(f"Local Documents Available:    {sum(1 for p in products if p['document_available']):>6d}")
    print("-" * 80)
    print("Sample Product Mappings:")
    for p in products[:10]:
        doc_badge = "📄 PDF" if p["document_available"] else "📑 META-ONLY"
        print(f"  • '{p['term']}' -> {p['standard_number']} ({p['current_edition']}) [{doc_badge}] (Conf: {p['confidence']})")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    build_products_registry()
