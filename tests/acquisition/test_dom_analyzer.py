"""
Automated Test Suite for DOM-Aware Structure Analyzer & Exhaustive Discovery (Phase 3).
Validates semantic region detection, table parsing, card extraction, navigation/footer chrome exclusion,
session gate detection, pagination tracking, and provenance evidence retention.
"""
import pytest
from ai.acquisition.discovery.dom_analyzer import DOMAnalyzer, DOMRecord, DOMDiscoveryEvidence, DOMAnalysisMetrics

# Fixture 1: BIS-style document listing
FIXTURE_DOC_LISTING = """
<!DOCTYPE html>
<html>
<head><title>Bureau of Indian Standards - Published Standards</title></head>
<body>
  <div class="site-wrapper">
    <main id="main-content">
      <section class="document-section">
        <h1>Electrotechnical Department Standards</h1>
        <ul class="standards-list">
          <li class="doc-item">
            <a href="https://www.bis.gov.in/standards/IS-374-2019.pdf">IS 374 : 2019 Electric Ceiling Fans - Specification</a>
            <span class="status">Active</span>
          </li>
          <li class="doc-item">
            <a href="https://www.bis.gov.in/standards/IS-16046-P2-2018.pdf">IS 16046 (Part 2) : 2018 Secondary Cells and Batteries</a>
            <span class="status">Active</span>
          </li>
        </ul>
      </section>
    </main>
  </div>
</body>
</html>
"""

# Fixture 2: BIS-style navigation + footer (pure chrome)
FIXTURE_NAV_FOOTER = """
<!DOCTYPE html>
<html>
<body>
  <header class="site-header">
    <nav class="main-navigation">
      <ul>
        <li><a href="https://www.bis.gov.in/">Home</a></li>
        <li><a href="https://www.bis.gov.in/about-us">About Us</a></li>
        <li><a href="https://www.bis.gov.in/contact-us">Contact Us</a></li>
        <li><a href="https://www.bis.gov.in/sitemap">Sitemap</a></li>
        <li><a href="https://www.bis.gov.in/feedback">Feedback</a></li>
      </ul>
    </nav>
  </header>
  <footer class="site-footer">
    <div class="footer-links">
      <a href="https://www.bis.gov.in/privacy-policy">Privacy Policy</a>
      <a href="https://www.bis.gov.in/terms-of-use">Terms of Use</a>
      <a href="https://www.bis.gov.in/disclaimer">Disclaimer</a>
    </div>
  </footer>
</body>
</html>
"""

# Fixture 3: Table-based laboratory registry (LIMS)
FIXTURE_TABLE_LAB_REGISTRY = """
<!DOCTYPE html>
<html>
<body>
  <main>
    <table class="lims-lab-table" id="labs-directory">
      <caption>BIS Recognized Testing Laboratories Directory</caption>
      <thead>
        <tr>
          <th>S.No</th><th>Lab ID</th><th>Laboratory Name</th><th>Address</th><th>Contact</th><th>Phone</th><th>Email</th><th>Validity</th><th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>1</td><td>8102006</td><td>SIIR, Delhi Shriram Institute For Industrial Research</td>
          <td>19-University Road, Delhi 110007</td><td>Dr. Laxmi Rawat</td><td>011 35200445</td>
          <td>laxmirawat@shriraminstitute.org</td><td>31 Dec, 2026</td>
          <td><a href="https://lims.bis.gov.in/home/view_scope/8102006">View Scope</a></td>
        </tr>
        <tr>
          <td>2</td><td>8138306</td><td>Testtex India Laboratories Private Limited, Noida</td>
          <td>C-57, Sector-65, Noida, UP</td><td>Amit Tiwari</td><td>7303919463</td>
          <td>labsindianoida@testtex.com</td><td>31 Dec, 2029</td>
          <td><a href="https://lims.bis.gov.in/home/view_scope/8138306">View Scope</a></td>
        </tr>
      </tbody>
    </table>
  </main>
</body>
</html>
"""

# Fixture 4: Card-based product/manual listing
FIXTURE_CARD_MANUAL_LISTING = """
<!DOCTYPE html>
<html>
<body>
  <main class="content-container">
    <h2>Product Manuals for Conformity Assessment</h2>
    <div class="manual-cards-grid">
      <div class="manual-box card">
        <h3 class="card-title">High Strength Deformed Steel Bars</h3>
        <p class="card-desc">Guidelines for certification of steel reinforcement bars conforming to IS 1786:2008.</p>
        <a class="btn-download" href="https://www.bis.gov.in/product-manuals/PM-IS-1786-2008-V1.pdf">Download Manual (PDF)</a>
      </div>
      <div class="manual-box card">
        <h3 class="card-title">Domestic Pressure Cookers</h3>
        <p class="card-desc">Product manual and testing guidelines for IS 2347:2017.</p>
        <a class="btn-download" href="https://www.bis.gov.in/product-manuals/PM-IS-2347-2017-V1.pdf">Download Manual (PDF)</a>
      </div>
    </div>
  </main>
</body>
</html>
"""

# Fixture 5: Search results with pagination
FIXTURE_SEARCH_PAGINATION = """
<!DOCTYPE html>
<html>
<body>
  <div class="search-results-wrapper">
    <h1>Quality Control Orders Search Results</h1>
    <div class="results-list">
      <div class="result-item">
        <a href="https://egazette.gov.in/gazette/QCO-DPIIT-SO1245E-2023.pdf">Steel Products QCO S.O. 1245(E)</a>
      </div>
      <div class="result-item">
        <a href="https://egazette.gov.in/gazette/QCO-DPIIT-SO3456E-2022.pdf">Cement QCO S.O. 3456(E)</a>
      </div>
    </div>
    <nav class="pagination" aria-label="pagination">
      <ul class="page-numbers">
        <li><span class="current">1</span></li>
        <li><a href="https://egazette.gov.in/search?page=2">2</a></li>
        <li><a href="https://egazette.gov.in/search?page=3">3</a></li>
      </ul>
    </nav>
  </div>
</body>
</html>
"""

# Fixture 6: Language selector elements
FIXTURE_LANG_SELECTOR = """
<!DOCTYPE html>
<html>
<body>
  <header>
    <div class="language-switcher">
      <a href="https://www.bis.gov.in/index.html?lang=en">English</a>
      <a href="https://www.bis.gov.in/index.html?lang=hi">हिन्दी</a>
    </div>
  </header>
  <main>
    <h1>Welcome to BIS</h1>
    <p>Official standards catalog</p>
  </main>
</body>
</html>
"""

# Fixture 7: Login / session-expiry page
FIXTURE_SESSION_EXPIRY = """
<!DOCTYPE html>
<html>
<head><title>Manakonline - Session Expired</title></head>
<body>
  <div class="auth-box" id="sessionExpire">
    <h2>Your Session Has Expired</h2>
    <p>Please re-login to access the licence database.</p>
    <form action="/MANAK/login" method="post">
      <input type="text" name="username">
      <input type="password" name="password">
      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html>
"""

# Fixture 8: Mixed content page (real documents + header + footer + sidebar + lang switch)
FIXTURE_MIXED_PAGE = """
<!DOCTYPE html>
<html>
<head><title>BIS Consumer Information Portal</title></head>
<body>
  <header class="navbar">
    <a href="https://www.bis.gov.in/">Home</a>
    <div class="lang-switch">
      <a href="https://www.bis.gov.in/consumer?lang=hi">हिन्दी</a>
    </div>
  </header>
  <div class="layout-wrapper">
    <aside class="sidebar">
      <ul>
        <li><a href="https://www.bis.gov.in/overview">Overview</a></li>
        <li><a href="https://www.bis.gov.in/faq">FAQs</a></li>
      </ul>
    </aside>
    <main class="content-body">
      <h1>Consumer Guidance Documents</h1>
      <article class="doc-card">
        <h3>BIS Care App User Manual</h3>
        <p>Complete guide on verifying ISI marks and hallmarking online.</p>
        <a href="https://www.bis.gov.in/consumer/BIS-Care-User-Manual.pdf">Download Guide (PDF)</a>
      </article>
      <article class="doc-card">
        <h3>Hallmarking Awareness Booklet</h3>
        <p>Consumer booklet on 6-digit HUID and gold purity.</p>
        <a href="https://www.bis.gov.in/consumer/Hallmarking-Consumer-Booklet.pdf">Download Booklet (PDF)</a>
      </article>
    </main>
  </div>
  <footer class="footer">
    <a href="https://www.bis.gov.in/sitemap">Sitemap</a>
    <a href="https://www.bis.gov.in/disclaimer">Disclaimer</a>
  </footer>
</body>
</html>
"""


class TestDOMAnalyzerDeterministicFixtures:
    """Validates the 8 core deterministic fixtures against the DOMAnalyzer."""

    def setup_method(self):
        self.analyzer = DOMAnalyzer()

    def test_fixture_1_document_listing_extracted(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_DOC_LISTING,
            "https://www.bis.gov.in/standards",
            "SRC-001",
            "SRCF-001"
        )
        assert len(records) == 2
        assert any("IS 374" in r.title for r in records)
        assert any("IS 16046" in r.title for r in records)
        for r in records:
            assert r.evidence is not None
            assert r.evidence.region_type in ["MAIN_CONTENT_LINK", "CARD_CONTAINER"]
            assert r.evidence.nearest_heading == "Electrotechnical Department Standards"

    def test_fixture_2_navigation_and_footer_excluded(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_NAV_FOOTER,
            "https://www.bis.gov.in/",
            "SRC-001",
            "SRCF-001"
        )
        assert len(records) == 0
        assert metrics.navigation_links_excluded >= 5
        assert metrics.footer_links_excluded >= 3

    def test_fixture_3_table_lab_registry_parsed(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_TABLE_LAB_REGISTRY,
            "https://lims.bis.gov.in/home/labs/",
            "SRC-013",
            "SRCF-008"
        )
        assert len(records) == 2
        assert metrics.document_regions >= 1
        for r in records:
            assert r.evidence is not None
            assert r.evidence.region_type == "TABLE_ROW"
            assert "SIIR" in r.title or "Testtex" in r.title or "View Scope" in r.title
            assert r.evidence.table_name == "BIS Recognized Testing Laboratories Directory"

    def test_fixture_4_card_manual_listing_parsed(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_CARD_MANUAL_LISTING,
            "https://www.bis.gov.in/product-manuals/",
            "SRC-006",
            "SRCF-004"
        )
        assert len(records) == 2
        assert metrics.document_regions >= 2
        for r in records:
            assert r.evidence is not None
            assert r.evidence.region_type == "CARD_CONTAINER"
            assert "Steel" in r.title or "Pressure Cookers" in r.title or "Download" in r.title

    def test_fixture_5_search_results_and_pagination_detected(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_SEARCH_PAGINATION,
            "https://egazette.gov.in/search",
            "SRC-004",
            "SRCF-003"
        )
        assert len(records) == 2
        assert metrics.pagination_detected is True
        assert metrics.pagination_pages >= 2
        assert any("Steel Products" in r.title for r in records)
        assert any("Cement QCO" in r.title for r in records)

    def test_fixture_6_language_selector_excluded(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_LANG_SELECTOR,
            "https://www.bis.gov.in/",
            "SRC-001",
            "SRCF-001"
        )
        assert len(records) == 0
        assert metrics.language_links_excluded >= 2

    def test_fixture_7_session_expiry_detected(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_SESSION_EXPIRY,
            "https://www.manakonline.in/MANAK/sessionExpire",
            "SRC-010",
            "SRCF-007"
        )
        assert len(records) == 0
        assert metrics.session_gated is True

    def test_fixture_8_mixed_page_extracts_content_and_rejects_noise(self):
        records, metrics = self.analyzer.analyze_dom(
            FIXTURE_MIXED_PAGE,
            "https://www.bis.gov.in/consumer",
            "SRC-016",
            "SRCF-010"
        )
        # Real document links extracted
        assert len(records) == 2
        assert any("BIS-Care" in r.url for r in records)
        assert any("Hallmarking-Consumer-Booklet" in r.url for r in records)
        # Noise excluded
        assert metrics.navigation_links_excluded >= 1
        assert metrics.footer_links_excluded >= 2
        assert metrics.sidebar_links_excluded >= 1
        assert metrics.language_links_excluded >= 1


class TestDOMAnalyzerExhaustiveProperties:
    """Validates structural evidence retention and absence of hardcoded lists."""

    def test_dom_evidence_fully_populated(self):
        analyzer = DOMAnalyzer()
        records, _ = analyzer.analyze_dom(
            FIXTURE_DOC_LISTING,
            "https://www.bis.gov.in/standards",
            "SRC-001",
            "SRCF-001"
        )
        ev = records[0].evidence
        assert ev is not None
        assert ev.source_page_url == "https://www.bis.gov.in/standards"
        assert ev.discovered_url.startswith("https://www.bis.gov.in/standards/IS-")
        assert ev.element_tag == "a"
        assert ev.nearest_heading == "Electrotechnical Department Standards"
        assert ev.container_tag in ["li", "ul", "section", "main", "div"]
        assert ev.discovery_reason != ""

    def test_metrics_serialization(self):
        analyzer = DOMAnalyzer()
        _, metrics = analyzer.analyze_dom(
            FIXTURE_MIXED_PAGE,
            "https://www.bis.gov.in/consumer",
            "SRC-016",
            "SRCF-010"
        )
        m_dict = metrics.to_dict()
        assert "raw_dom_elements" in m_dict
        assert "raw_links" in m_dict
        assert "navigation_links_excluded" in m_dict
        assert "footer_links_excluded" in m_dict
        assert "valid_candidates" in m_dict
        assert m_dict["valid_candidates"] == 2
