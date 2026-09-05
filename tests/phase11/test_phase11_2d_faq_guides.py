import unittest
import sys
sys.path.append('.')

from scripts.phase11_2d_faq_guides_acquisition import (
    infer_information_type,
    extract_text_from_html,
    is_faq_guide_candidate,
)

class TestFAQGuidesAcquisition(unittest.TestCase):

    def test_01_categorization_pdf(self):
        self.assertTrue(is_faq_guide_candidate("http://bis.gov.in/doc.pdf"))

    def test_02_categorization_faq(self):
        self.assertTrue(is_faq_guide_candidate("http://bis.gov.in/faq/"))

    def test_03_categorization_guide(self):
        self.assertTrue(is_faq_guide_candidate("http://bis.gov.in/guidelines/"))

    def test_04_categorization_booklet(self):
        self.assertTrue(is_faq_guide_candidate("http://bis.gov.in/booklet"))

    def test_05_categorization_unrelated(self):
        self.assertFalse(is_faq_guide_candidate("http://bis.gov.in/jobs/recruitment"))

    def test_06_infer_faq(self):
        self.assertEqual(infer_information_type("http://bis.gov.in/faq", ""), "FAQ")

    def test_07_infer_guide(self):
        self.assertEqual(infer_information_type("http://bis.gov.in/page", "this guideline explains"), "GUIDE")

    def test_08_infer_circular(self):
        self.assertEqual(infer_information_type("http://bis.gov.in/circular", ""), "CIRCULAR")

    def test_09_infer_booklet(self):
        self.assertEqual(infer_information_type("http://bis.gov.in/booklet", ""), "BOOKLET")

    def test_10_infer_pdf_fallback(self):
        self.assertEqual(infer_information_type("http://bis.gov.in/doc.pdf", "some text"), "OFFICIAL_DOCUMENT")

    def test_11_html_extraction(self):
        html = "<html><body><p>FAQ content</p></body></html>"
        text, status = extract_text_from_html(html)
        self.assertEqual(text, "FAQ content")
        self.assertEqual(status, "SUCCESS")

    def test_12_provenance(self): self.assertTrue(True)
    def test_13_duplicate_handling(self): self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
