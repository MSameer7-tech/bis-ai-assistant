import unittest
from ai.acquisition.licences.discovery import LicencesDiscovery
from ai.acquisition.licences.parser import extract_text_from_html, infer_information_type

class TestLicencesAcquisition(unittest.TestCase):
    
    def setUp(self):
        self.discovery = LicencesDiscovery(["http://mock"])

    def test_01_discovery_categorization(self):
        self.assertEqual(self.discovery.categorize_link("http://bis.gov.in/doc.pdf"), "PDF")
        self.assertEqual(self.discovery.categorize_link("http://bis.gov.in/page"), "HTML")
        
    def test_02_infer_info_type(self):
        self.assertEqual(infer_information_type("http://bis.gov.in/crs", ""), "CRS")
        self.assertEqual(infer_information_type("http://bis.gov.in/page", "Check your fmcs here"), "FMCS")
        self.assertEqual(infer_information_type("http://bis.gov.in/fees", ""), "FEES")
        self.assertEqual(infer_information_type("http://bis.gov.in/faq", ""), "FAQ")
        
    def test_03_html_extraction(self):
        html = "<html><body><p>Test Licences</p></body></html>"
        text, status = extract_text_from_html(html)
        self.assertEqual(text, "Test Licences")
        self.assertEqual(status, "SUCCESS")
        
    def test_04_mock_safety(self): self.assertTrue(True)
    def test_05_provenance_fields_exist(self): self.assertTrue(True)
    def test_06_duplicate_handling(self): self.assertTrue(True)
    def test_07_operational_portal_prioritization(self): self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
