import pytest
from bs4 import BeautifulSoup
from ai.acquisition.discovery.http_catalog_discovery import (
    HTTPCatalogDiscovery,
    extract_tables_from_html,
    detect_completeness,
    is_bis_domain
)

def test_is_bis_domain():
    assert is_bis_domain("https://www.bis.gov.in/test") == True
    assert is_bis_domain("http://bis.gov.in") == True
    assert is_bis_domain("https://google.com") == False

def test_extract_tables_headers_and_rows():
    html = """
    <html>
        <body>
            <table>
                <tr><th>IS Number</th><th>Product Name</th></tr>
                <tr><td>IS 1000</td><td>Test Product</td></tr>
                <tr><td>IS 2000</td><td></td></tr>
            </table>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    tables = extract_tables_from_html(soup)
    assert len(tables) == 1
    assert len(tables[0]) == 2
    assert tables[0][0]["IS Number"] == "IS 1000"
    assert tables[0][0]["Product Name"] == "Test Product"
    # Testing provenance
    assert "<tr><td>IS 1000</td><td>Test Product</td></tr>" in tables[0][0]["_raw_html"]

def test_extract_tables_variable_ordering():
    html = """
    <table>
        <tr><th>Product</th><th>Description</th><th>Standard</th></tr>
        <tr><td>Item A</td><td>Desc A</td><td>IS A</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    tables = extract_tables_from_html(soup)
    assert tables[0][0]["Product"] == "Item A"
    assert tables[0][0]["Standard"] == "IS A"

def test_extract_tables_malformed_and_duplicate_headers():
    html = """
    <table>
        <tr><th>Product</th><th>Product</th></tr>
        <tr><td>Item 1</td><td>Item 2</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    tables = extract_tables_from_html(soup)
    assert tables[0][0]["Product"] == "Item 1"
    assert tables[0][0]["Product_2"] == "Item 2"

def test_detect_completeness():
    # Empty table
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert detect_completeness(soup, 0, 0) == "EMPTY"
    
    # Paginated explicitly
    soup = BeautifulSoup("<html><div class='pagination'>Next</div></html>", "html.parser")
    assert detect_completeness(soup, 1, 10) == "PAGINATED"
    
    # API required
    soup = BeautifulSoup("<html><script>$(tbl).DataTable({ajax: 'url'})</script></html>", "html.parser")
    assert detect_completeness(soup, 1, 10) == "DYNAMIC_API_REQUIRED"
    
    # Complete
    soup = BeautifulSoup("<html><body><table></table></body></html>", "html.parser")
    assert detect_completeness(soup, 1, 900) == "COMPLETE_STATIC_HTML"

def test_relationship_extraction():
    discovery = HTTPCatalogDiscovery()
    scheme_info = {
        "scheme_name": "Scheme I",
        "final_url": "https://bis.gov.in/scheme-i",
        "response_sha256": "abc123hash"
    }
    
    # Variable column ordering and missing/blank data
    tables = [
        [
            {"Product Name": "Test A", "Indian Standard": "IS 1111", "_raw_html": "raw1"},
            {"Product": "Test B", "IS No.": "IS 2222", "_raw_html": "raw2"},
            {"Product": "-", "IS No.": "-", "_raw_html": "raw3"} # blank
        ]
    ]
    
    rels = discovery.extract_structured_relationships(scheme_info, tables)
    assert len(rels) == 2
    assert rels[0]["product_name"] == "Test A"
    assert rels[0]["standard_number"] == "IS 1111"
    assert rels[0]["source_sha256"] == "abc123hash"
    assert rels[0]["source_url"] == "https://bis.gov.in/scheme-i"
    assert rels[0]["discovery_evidence"] == "raw1"
    
    assert rels[1]["product_name"] == "Test B"
    assert rels[1]["standard_number"] == "IS 2222"

def test_landing_page_discovery(monkeypatch):
    import requests
    
    class MockResponse:
        def __init__(self, text, url):
            self.text = text
            self.content = text.encode("utf-8")
            self.url = url
            self.status_code = 200
            
        def raise_for_status(self):
            pass
            
    def mock_get(url, *args, **kwargs):
        html = """
        <html>
            <a href="scheme-i-mark/">Scheme I Mark Scheme</a>
            <a href="/scheme-ii/">Scheme II Registration</a>
            <a href="https://other.com/bad">External</a>
            <a href="scheme-i-mark/">Duplicate Link</a>
            <a href="guidelines.pdf">PDF Guideline</a>
        </html>
        """
        return MockResponse(html, url)
        
    monkeypatch.setattr(requests, "get", mock_get)
    
    discovery = HTTPCatalogDiscovery()
    schemes = discovery.discover_schemes("https://www.bis.gov.in/landing/")
    
    assert len(schemes) == 2
    # Relative URL resolution
    urls = [s["discovered_url"] for s in schemes]
    assert "https://www.bis.gov.in/landing/scheme-i-mark/" in urls
    assert "https://www.bis.gov.in/scheme-ii/" in urls
    # Deduplication check
    assert len([u for u in urls if "scheme-i-mark" in u]) == 1
    # PDF ignored
    assert not any(".pdf" in u for u in urls)
    # External ignored
    assert not any("other.com" in u for u in urls)
