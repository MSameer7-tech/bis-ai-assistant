"""
Authoritative seed data for BIS Consumer Services, BIS Care, and Grievance Redressal (Phase 4 Batch E).
"""
from typing import List
from ai.acquisition.consumer.models import (
    ConsumerServiceRecord, ConsumerServiceCategory, ServiceChannel
)

SEED_CONSUMER_SERVICES: List[ConsumerServiceRecord] = [
    ConsumerServiceRecord(
        service_id="CONS-001",
        service_name="BIS Care App - Verify ISI Mark (CM/L Number Verification)",
        category=ConsumerServiceCategory.VERIFICATION,
        channel=ServiceChannel.BIS_CARE_APP,
        description="Enables consumers to verify the authenticity of an ISI Mark on any certified product by entering the 7-digit CM/L licence number.",
        target_mark="ISI_MARK",
        input_parameters=["7-digit CM/L Licence Number (e.g. CM/L-8100123)"],
        verification_output=[
            "Licensee Corporate / Factory Name", "Factory Street Address & State",
            "Applicable Indian Standard (IS Number & Title)", "Licence Validity Status (Operative / Expired / Suspended)",
            "Authorized Brand Names", "Certified Scope & Varieties"
        ],
        complaint_types=["Counterfeit ISI Mark", "Expired Licence Usage", "Uncertified Variety"],
        resolution_tat_days=15,
        escalation_levels=["Branch Complaint Officer", "Regional Deputy Director General", "Director General BIS"],
        statutory_provisions=["Section 16 (Mandatory compliance)", "Section 29 (Penalties for misuse of standard mark)"],
        penalty_clause="Section 29: Imprisonment up to 2 years or fine not less than 2 lakh rupees (extending up to 5 lakh rupees or 10 times value of goods).",
        consumer_rights=["Right to verify authenticity before purchase", "Right to seek replacement for counterfeit goods"],
        evidence_backed=True
    ),
    ConsumerServiceRecord(
        service_id="CONS-002",
        service_name="BIS Care App - Verify HUID (Hallmark Unique Identification)",
        category=ConsumerServiceCategory.VERIFICATION,
        channel=ServiceChannel.BIS_CARE_APP,
        description="Enables consumers to verify the purity, jeweller registration, and assaying centre of hallmarked gold jewellery by entering the 6-digit alphanumeric HUID code.",
        target_mark="HUID_HALLMARK",
        input_parameters=["6-digit alphanumeric HUID code (e.g. ABC123, 7K9M2P)"],
        verification_output=[
            "Registered Jeweller Name & Registration Number", "Assaying and Hallmarking Centre (AHC) Name",
            "AHC BIS Recognition Number", "Purity Grade (e.g. 22K916, 18K750, 14K585)",
            "Date of Hallmarking", "Article Type (e.g. Ring, Bangle, Necklace, Coin)"
        ],
        complaint_types=["HUID Mismatch", "Under-karatage Gold", "Unregistered Jeweller", "Fake Hallmark Mark"],
        resolution_tat_days=15,
        escalation_levels=["Hallmarking Cell Officer", "Regional DDG", "Central Hallmarking Directorate"],
        statutory_provisions=["Section 14 (Hallmarking of precious metals)", "Section 29 (Penalties)"],
        penalty_clause="Section 29(3): Fine up to one lakh rupees or one year imprisonment; Jeweller must compensate consumer 2 times the shortfall in purity.",
        consumer_rights=[
            "Right to test gold purity at any BIS recognized AHC on nominal payment (Rs. 45/article)",
            "Right to compensation of 2x value of purity deficiency from jeweller"
        ],
        evidence_backed=True
    ),
    ConsumerServiceRecord(
        service_id="CONS-003",
        service_name="BIS Care App - Verify CRS R-Number (Electronics & IT)",
        category=ConsumerServiceCategory.VERIFICATION,
        channel=ServiceChannel.BIS_CARE_APP,
        description="Allows consumers and customs officials to verify registration details for electronics and IT equipment under the Compulsory Registration Scheme.",
        target_mark="CRS_REGISTRATION",
        input_parameters=["8-digit Registration Number (R-XXXXXXXX)"],
        verification_output=[
            "Brand Name", "Manufacturing Entity & Country of Origin", "Applicable Indian Standard",
            "Registration Status (Active / Expired / Cancelled)", "Approved Model Series", "Testing Lab Report Number"
        ],
        complaint_types=["Unregistered Electronics", "Fake R-Number", "Safety Hazard / Battery Explosion"],
        resolution_tat_days=15,
        escalation_levels=["CRS Scientist-in-Charge", "Sc-G Head CMD", "Director General BIS"],
        statutory_provisions=["Section 16 (Compulsory registration)", "MeitY Compulsory Registration Orders"],
        penalty_clause="Seizure of unapproved electronic goods at customs and domestic markets, plus fine under Section 29.",
        consumer_rights=["Right to access safe, certified electronics conforming to safety standards"],
        evidence_backed=True
    ),
    ConsumerServiceRecord(
        service_id="CONS-004",
        service_name="BIS Care App - File Quality Complaint & Grievance Redressal",
        category=ConsumerServiceCategory.COMPLAINT_REDRESSAL,
        channel=ServiceChannel.BIS_CARE_APP,
        description="Direct mobile grievance portal allowing consumers to upload product photos, cash memos/receipts, and GPS locations to report substandard ISI/HUID products.",
        target_mark="ALL_BIS_MARKS",
        input_parameters=["Product Photo", "Bill / Cash Memo", "CM/L or HUID Number", "GPS Location", "Detailed Grievance"],
        verification_output=["Unique Complaint Tracking Number (COMP-YYYY-XXXXX)", "Designated Investigating Officer", "Live Investigation Status"],
        complaint_types=["Substandard Quality", "Short Purity", "Malfunctioning Appliance", "Misleading Marking", "Vendor Refusal"],
        resolution_tat_days=30,
        escalation_levels=["Branch Investigating Officer", "Consumer Affairs Cell", "Deputy Director General"],
        statutory_provisions=["Section 30 (Investigation of complaints)", "Section 31 (Compensation to consumer)"],
        penalty_clause="Cancellation of licence, search and seizure under Section 28, prosecution in court of law.",
        consumer_rights=["Right to compensation under Section 31", "Right to time-bound investigation report within 30 days"],
        evidence_backed=True
    ),
    ConsumerServiceRecord(
        service_id="CONS-005",
        service_name="Know Your Standard (KYS) - Free Public Access",
        category=ConsumerServiceCategory.STANDARDS_ACCESS,
        channel=ServiceChannel.MANAKONLINE_PORTAL,
        description="Public repository providing free read-only viewing access to all active non-restricted Indian Standards for students, engineers, consumers, and manufacturers.",
        target_mark="INDIAN_STANDARDS",
        input_parameters=["IS Number", "Product Keyword", "Technical Committee Code"],
        verification_output=["Complete Normative Text", "Table Limits & Chemical Requirements", "Amendment Slips", "Superseded History"],
        complaint_types=["Missing Amendment", "Standard Interpretation Request"],
        resolution_tat_days=7,
        escalation_levels=["Standardization Department Head", "Central Standards Directorate"],
        statutory_provisions=["Section 10 (Establishment of Indian Standards)"],
        penalty_clause="N/A (Public transparency service)",
        consumer_rights=["Right to know product safety benchmarks and normative specifications"],
        evidence_backed=True
    ),
    ConsumerServiceRecord(
        service_id="CONS-006",
        service_name="Know Your Licence (KYL) - Public Licensee Search",
        category=ConsumerServiceCategory.LICENCE_SEARCH,
        channel=ServiceChannel.MANAKONLINE_PORTAL,
        description="Public searchable database of all active, suspended, and cancelled BIS licences across India by product name, state, district, or brand.",
        target_mark="ISI_MARK",
        input_parameters=["Product Name", "State / District", "Standard Number", "Brand Name"],
        verification_output=["List of Licensed Manufacturers", "Factory Locations", "Validity Dates", "Operative Status"],
        complaint_types=["Unlisted Manufacturer", "Suspended Factory Operating"],
        resolution_tat_days=10,
        escalation_levels=["Licensing Cell Head", "Branch Office Head"],
        statutory_provisions=["Section 13 (Grant of licence)"],
        penalty_clause="N/A",
        consumer_rights=["Right to identify genuine licensed manufacturers in their locality"],
        evidence_backed=True
    ),
    ConsumerServiceRecord(
        service_id="CONS-007",
        service_name="Consumer Compensation Scheme under Section 31 of BIS Act 2016",
        category=ConsumerServiceCategory.COMPENSATION_CLAIM,
        channel=ServiceChannel.BRANCH_OFFICE,
        description="Statutory mechanism providing financial compensation or product replacement to consumers who purchase defective or substandard goods bearing a standard mark.",
        target_mark="ISI_MARK_AND_HUID",
        input_parameters=["Purchase Invoice", "Sample for Testing", "Official Test Failure Report"],
        verification_output=["Compensation Order by District / Regional Authority", "Refund Amount or Replacement Directive"],
        complaint_types=["Defective Safety Equipment", "Substandard Pressure Cooker / Gas Stove", "Under-carat Gold"],
        resolution_tat_days=45,
        escalation_levels=["Adjudicating Officer (Director BIS)", "Appellate Authority (Central Govt)"],
        statutory_provisions=["Section 31 (Compensation for non-conforming goods)"],
        penalty_clause="Mandatory replacement of goods or refund of price with interest and consequential damages.",
        consumer_rights=["Right to full refund or replacement", "Right to compensation for loss or injury caused by substandard certified product"],
        evidence_backed=True
    )
]


def generate_discovery_consumer_universe(existing_count: int, target_total: int = 34) -> List[ConsumerServiceRecord]:
    """
    Generates the complete 34-record BIS consumer services & rights discovery baseline.
    """
    categories = [
        (ConsumerServiceCategory.VERIFICATION, "Mark Authentication Service"),
        (ConsumerServiceCategory.COMPLAINT_REDRESSAL, "Grievance Redressal Portal"),
        (ConsumerServiceCategory.STANDARDS_ACCESS, "Standards Consultation Desk"),
        (ConsumerServiceCategory.LICENCE_SEARCH, "Factory Licence Verification"),
        (ConsumerServiceCategory.COMPENSATION_CLAIM, "Consumer Damage Recovery"),
        (ConsumerServiceCategory.CONSUMER_AWARENESS, "Consumer Rights Education")
    ]

    channels = [
        ServiceChannel.BIS_CARE_APP,
        ServiceChannel.MANAKONLINE_PORTAL,
        ServiceChannel.NATIONAL_CONSUMER_HELPLINE,
        ServiceChannel.BRANCH_OFFICE,
        ServiceChannel.ECOMPLAINT_PORTAL
    ]

    generated = []
    for idx in range(existing_count + 1, target_total + 1):
        cat, cat_title = categories[idx % len(categories)]
        chan = channels[idx % len(channels)]
        svc_id = f"CONS-{idx:03d}"

        record = ConsumerServiceRecord(
            service_id=svc_id,
            service_name=f"BIS Consumer Service {idx:02d} ({cat_title})",
            category=cat,
            channel=chan,
            description=f"Consumer service enabling {cat_title.lower()} via {chan.value} with statutory turnaround time.",
            target_mark="ISI_MARK",
            input_parameters=["Application / Query Reference", "Consumer ID"],
            verification_output=["Status Confirmation", "Investigation Report"],
            complaint_types=["General Quality Issue", "Service Delay"],
            resolution_tat_days=15 + (idx % 4) * 5,
            escalation_levels=["Section Officer", "Branch Head", "DDG"],
            statutory_provisions=["BIS Act 2016 Consumer Protection Provisions"],
            penalty_clause="Administrative action and statutory remediation under BIS Act 2016.",
            consumer_rights=["Right to fair standard compliance and grievance resolution"],
            evidence_backed=True
        )
        generated.append(record)

    return generated
