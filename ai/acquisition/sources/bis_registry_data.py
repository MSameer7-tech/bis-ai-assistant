"""
Authoritative BIS Registry Data Definitions.
Provides structured databases for:
1. Statutory Quality Control Orders (QCOs) & Gazette Notifications
2. BIS Central, Regional, Branch & Recognized Testing Laboratories
3. BIS Division Councils and Technical Sectional Committees
"""

QCO_DATABASE = [
    {
        "qco_id": "QCO-DPIIT-FANS-2023",
        "title": "Electric Ceiling Fans (Quality Control) Order, 2023",
        "ministry": "Ministry of Commerce and Industry (DPIIT)",
        "enforcement_date": "2024-01-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 374",
        "source_url": "https://bis.gov.in/qco/ceiling_fans_2023.pdf"
    },
    {
        "qco_id": "QCO-STEEL-REBARS-2024",
        "title": "Steel and Steel Products (Quality Control) Order, 2024",
        "ministry": "Ministry of Steel",
        "enforcement_date": "2024-09-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 1786, IS 2062",
        "source_url": "https://steel.gov.in/qco/steel_products_2024.pdf"
    },
    {
        "qco_id": "QCO-DPIIT-CEMENT-2024",
        "title": "Cement (Quality Control) Order, 2024",
        "ministry": "Ministry of Commerce and Industry (DPIIT)",
        "enforcement_date": "2024-03-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 269, IS 1489 Part 1, IS 1489 Part 2, IS 455",
        "source_url": "https://bis.gov.in/qco/cement_2024.pdf"
    },
    {
        "qco_id": "QCO-MORTH-HELMETS-2021",
        "title": "Two-Wheeler Protective Helmets (Quality Control) Order, 2021",
        "ministry": "Ministry of Road Transport and Highways (MoRTH)",
        "enforcement_date": "2021-06-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 4151",
        "source_url": "https://morth.gov.in/qco/helmets_2021.pdf"
    },
    {
        "qco_id": "QCO-MEITY-BATTERIES-2021",
        "title": "Electronics and IT Goods (Compulsory Registration) Order - Secondary Lithium Cells",
        "ministry": "Ministry of Electronics and Information Technology (MeitY)",
        "enforcement_date": "2021-04-01",
        "statutory_scheme": "Scheme II (CRS Mark)",
        "standard_number": "IS 16046 Part 1, IS 16046 Part 2",
        "source_url": "https://meity.gov.in/cro/lithium_batteries.pdf"
    },
    {
        "qco_id": "QCO-DPIIT-TOYS-2020",
        "title": "Toys (Quality Control) Order, 2020",
        "ministry": "Ministry of Commerce and Industry (DPIIT)",
        "enforcement_date": "2021-01-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 9873 Part 1, IS 9873 Part 2, IS 9873 Part 3, IS 15644",
        "source_url": "https://bis.gov.in/qco/toys_2020.pdf"
    },
    {
        "qco_id": "QCO-DPIIT-FOOTWEAR-2023",
        "title": "Footwear made from Leather and other materials (Quality Control) Order, 2023",
        "ministry": "Ministry of Commerce and Industry (DPIIT)",
        "enforcement_date": "2024-01-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 15844, IS 3738, IS 1988",
        "source_url": "https://bis.gov.in/qco/footwear_2023.pdf"
    },
    {
        "qco_id": "QCO-DPIIT-COOKERS-2020",
        "title": "Domestic Pressure Cookers (Quality Control) Order, 2020",
        "ministry": "Ministry of Commerce and Industry (DPIIT)",
        "enforcement_date": "2021-02-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 2347",
        "source_url": "https://bis.gov.in/qco/pressure_cookers_2020.pdf"
    },
    {
        "qco_id": "QCO-DPIIT-CABLES-2023",
        "title": "Electrical Wires, Cables and Appliances (Quality Control) Order, 2023",
        "ministry": "Ministry of Commerce and Industry (DPIIT)",
        "enforcement_date": "2023-12-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 694, IS 1554 Part 1, IS 7098 Part 1",
        "source_url": "https://bis.gov.in/qco/cables_2023.pdf"
    },
    {
        "qco_id": "QCO-DPIIT-SOLAR-2018",
        "title": "Solar Photovoltaics, Systems, Devices and Components (Requirement for Compulsory Use of Standard Mark) Order, 2018",
        "ministry": "Ministry of New and Renewable Energy (MNRE)",
        "enforcement_date": "2019-01-01",
        "statutory_scheme": "Scheme II (CRS Mark)",
        "standard_number": "IS 14286, IS/IEC 61730 Part 1, IS/IEC 61730 Part 2",
        "source_url": "https://mnre.gov.in/qco/solar_pv_2018.pdf"
    },
    {
        "qco_id": "QCO-FSSAI-WATER-2024",
        "title": "Packaged Drinking Water (Compulsory Certification) Order, 2024",
        "ministry": "Food Safety and Standards Authority of India (FSSAI) & MoHFW",
        "enforcement_date": "2024-07-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 14543, IS 13428",
        "source_url": "https://fssai.gov.in/qco/packaged_drinking_water.pdf"
    },
    {
        "qco_id": "QCO-DPIIT-GAS-STOVES-2021",
        "title": "Domestic Gas Stoves for use with Liquefied Petroleum Gases (Quality Control) Order, 2021",
        "ministry": "Ministry of Commerce and Industry (DPIIT)",
        "enforcement_date": "2022-01-01",
        "statutory_scheme": "Scheme I (ISI Mark)",
        "standard_number": "IS 4246",
        "source_url": "https://bis.gov.in/qco/gas_stoves_2021.pdf"
    }
]

LABORATORY_DATABASE = [
    {
        "lab_id": "LAB-001",
        "name": "Central Laboratory Sahibabad (CL)",
        "location": "Sahibabad, Ghaziabad, Uttar Pradesh",
        "lab_type": "central",
        "capabilities": "Chemical, Electrical, Mechanical, Microbiology, Food, Civil, Electronics"
    },
    {
        "lab_id": "LAB-002",
        "name": "Western Regional Office Laboratory (WROL)",
        "location": "Andheri East, Mumbai, Maharashtra",
        "lab_type": "regional",
        "capabilities": "Chemical, Electrical, Mechanical, Microbiology, Polymer, Gold Assay"
    },
    {
        "lab_id": "LAB-003",
        "name": "Eastern Regional Office Laboratory (EROL)",
        "location": "Salt Lake, Kolkata, West Bengal",
        "lab_type": "regional",
        "capabilities": "Chemical, Electrical, Mechanical, Metallurgical, Food"
    },
    {
        "lab_id": "LAB-004",
        "name": "Southern Regional Office Laboratory (SROL)",
        "location": "CIT Campus, Taramani, Chennai, Tamil Nadu",
        "lab_type": "regional",
        "capabilities": "Electrical, Electronics, Mechanical, Chemical, Medical Devices"
    },
    {
        "lab_id": "LAB-005",
        "name": "Northern Regional Office Laboratory (NROL)",
        "location": "Sector 19, Mohali, Punjab / Chandigarh",
        "lab_type": "regional",
        "capabilities": "Mechanical, Civil (Cement/Concrete), Electrical, Chemical"
    },
    {
        "lab_id": "LAB-006",
        "name": "Bengaluru Branch Office Laboratory (BNBO)",
        "location": "Peenya Industrial Area, Bengaluru, Karnataka",
        "lab_type": "branch",
        "capabilities": "Electronics, Information Technology, Secondary Cells, Solar Inverters"
    },
    {
        "lab_id": "LAB-007",
        "name": "Patna Branch Office Laboratory (PABO)",
        "location": "Pataliputra Industrial Area, Patna, Bihar",
        "lab_type": "branch",
        "capabilities": "Chemical, Packaged Drinking Water, Food, Civil"
    },
    {
        "lab_id": "LAB-008",
        "name": "Guwahati Branch Office Laboratory (GBO)",
        "location": "Panjabari, Guwahati, Assam",
        "lab_type": "branch",
        "capabilities": "Water, Food, Microbiology, General Chemical"
    },
    {
        "lab_id": "LAB-009",
        "name": "National Physical Laboratory (NPL India - NABL Partner)",
        "location": "New Delhi",
        "lab_type": "recognized_partner",
        "capabilities": "Primary Metrology, High Precision Reference Calibration, Photometry, Quantum Standards"
    }
]

COMMITTEE_DATABASE = [
    {
        "committee_id": "COMM-01",
        "department_code": "ETD",
        "committee_code": "ETD 01",
        "title": "Basic Electrotechnical Standards Sectional Committee",
        "scope": "Voltages, currents, frequencies, graphical symbols, quantities and units."
    },
    {
        "committee_id": "COMM-02",
        "department_code": "ETD",
        "committee_code": "ETD 05",
        "title": "Electric Fans Sectional Committee",
        "scope": "Ceiling fans, table fans, pedestal fans, exhaust fans, and air circulators."
    },
    {
        "committee_id": "COMM-03",
        "department_code": "CED",
        "committee_code": "CED 02",
        "title": "Cement and Concrete Sectional Committee",
        "scope": "Ordinary Portland Cement, Portland Pozzolana Cement, Slag Cement, Concrete Mix Design."
    },
    {
        "committee_id": "COMM-04",
        "department_code": "MTD",
        "committee_code": "MTD 04",
        "title": "Wrought Steel Products Sectional Committee",
        "scope": "High strength deformed steel bars (TMT), structural steel, billets, wire rods."
    },
    {
        "committee_id": "COMM-05",
        "department_code": "MED",
        "committee_code": "MED 04",
        "title": "Domestic and Commercial Gas Burning Appliances Sectional Committee",
        "scope": "LPG gas stoves, gas geysers, industrial burners, pressure cookers."
    },
    {
        "committee_id": "COMM-06",
        "department_code": "LITD",
        "committee_code": "LITD 10",
        "title": "Audio, Video and Multimedia Systems Sectional Committee",
        "scope": "Televisions, audio amplifiers, multimedia servers, safety requirements."
    },
    {
        "committee_id": "COMM-07",
        "department_code": "LITD",
        "committee_code": "LITD 12",
        "title": "Secondary Cells and Batteries Sectional Committee",
        "scope": "Lithium-ion cells, lead acid storage batteries, nickel metal hydride batteries."
    },
    {
        "committee_id": "COMM-08",
        "department_code": "CHD",
        "committee_code": "CHD 13",
        "title": "Drinking Water Sectional Committee",
        "scope": "Packaged drinking water, natural mineral water, municipal water standards."
    },
    {
        "committee_id": "COMM-09",
        "department_code": "FAD",
        "committee_code": "FAD 15",
        "title": "Food Hygiene, Safety Management and Other Systems Sectional Committee",
        "scope": "HACCP, food hygiene, dairy products, edible oils."
    },
    {
        "committee_id": "COMM-10",
        "department_code": "MHD",
        "committee_code": "MHD 09",
        "title": "Personal Safety Equipment (PPE) Sectional Committee",
        "scope": "Protective helmets, safety harnesses, work boots, protective gloves."
    },
    {
        "committee_id": "COMM-11",
        "department_code": "TXD",
        "committee_code": "TXD 14",
        "title": "Textile Materials for Industrial & Technical Applications Sectional Committee",
        "scope": "Geotextiles, medical textiles, fire retardant fabrics, protective clothing."
    },
    {
        "committee_id": "COMM-12",
        "department_code": "PRD",
        "committee_code": "PRD 03",
        "title": "Metrology and Precision Measurement Sectional Committee",
        "scope": "Limit gauges, precision micrometers, dial gauges, surface texture measurement."
    }
]
