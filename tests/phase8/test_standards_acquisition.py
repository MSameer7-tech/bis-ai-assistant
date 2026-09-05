import pytest
import json
import hashlib
from unittest.mock import patch, MagicMock

def normalize_standard(std):
    std = std.strip()
    return ' '.join(std.split())

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

class TestStandardAcquisition:
    def test_normalization(self):
        assert normalize_standard("IS  15750") == "IS 15750"
        assert normalize_standard(" IS 1234 (Part 1) : 2020 ") == "IS 1234 (Part 1) : 2020"
        
    def test_deduplication(self):
        inputs = ["IS 15750", "IS  15750", "IS 15750 "]
        normalized = set(normalize_standard(s) for s in inputs)
        assert len(normalized) == 1
        assert list(normalized)[0] == "IS 15750"

    @patch('requests.post')
    @patch('requests.get')
    def test_successful_acquisition(self, mock_get, mock_post):
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'd': [
                '{"First":"BIS -- IS 15750 : 2006","Second":"Standard_Number=IS+15750&id=8074"}'
            ]
        }
        mock_post.return_value = mock_post_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.text = """
        <html>
            <body>
                <span id="ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstdno_rptr">IS 15750 : 2006</span>
                <span id="ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblreaff">2022</span>
                <span id="ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstatus">withdrawn</span>
            </body>
        </html>
        """
        mock_get.return_value = mock_get_response

        from scripts.acquire_standards_metadata import process_standard
        
        record = process_standard("IS 15750")
        assert record['acquisition']['status'] == 'SUCCESS'
        assert record['internal_bis_id'] == '8074'
        assert record['standard_number'] == 'IS 15750 : 2006'
        assert record['status'] == 'withdrawn'
        assert record['reaffirmed_year'] == '2022'
        assert 'source_sha256' in record['source']
        
    @patch('requests.post')
    def test_resolver_not_found(self, mock_post):
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {'d': []}
        mock_post.return_value = mock_post_response
        
        from scripts.acquire_standards_metadata import process_standard
        record = process_standard("IS 99999")
        assert record['acquisition']['status'] == 'RESOLUTION_FAILED'
        
    @patch('requests.post')
    def test_resolver_malformed_json(self, mock_post):
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_post_response
        
        from scripts.acquire_standards_metadata import process_standard
        record = process_standard("IS 15750")
        assert record['acquisition']['status'] == 'RESOLUTION_FAILED'

    @patch('requests.post')
    def test_resolver_missing_id(self, mock_post):
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'd': [
                '{"First":"BIS -- IS 15750 : 2006","Second":"Standard_Number=IS+15750"}'
            ]
        }
        mock_post.return_value = mock_post_response
        
        from scripts.acquire_standards_metadata import process_standard
        record = process_standard("IS 15750")
        assert record['acquisition']['status'] == 'RESOLUTION_FAILED'

    @patch('requests.post')
    @patch('requests.get')
    def test_metadata_fetch_failure(self, mock_get, mock_post):
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'd': ['{"First":"BIS -- IS 15750 : 2006","Second":"Standard_Number=IS+15750&id=8074"}']
        }
        mock_post.return_value = mock_post_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 500
        mock_get.return_value = mock_get_response

        from scripts.acquire_standards_metadata import process_standard
        record = process_standard("IS 15750")
        assert record['acquisition']['status'] == 'METADATA_FETCH_FAILED'
        
    @patch('requests.post')
    @patch('requests.get')
    def test_metadata_malformed_page(self, mock_get, mock_post):
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'd': ['{"First":"BIS -- IS 15750 : 2006","Second":"Standard_Number=IS+15750&id=8074"}']
        }
        mock_post.return_value = mock_post_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.text = "<html><body>No useful metadata here</body></html>"
        mock_get.return_value = mock_get_response

        from scripts.acquire_standards_metadata import process_standard
        record = process_standard("IS 15750")
        assert record['acquisition']['status'] == 'PARSE_FAILED'

    @patch('requests.post')
    @patch('requests.get')
    def test_identity_mismatch(self, mock_get, mock_post):
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'd': ['{"First":"BIS -- IS 15750 : 2006","Second":"Standard_Number=IS+15750&id=8074"}']
        }
        mock_post.return_value = mock_post_response

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.text = """
        <html>
            <body>
                <span id="ctl00_ContentPlaceHolder1_T1_Repeater1_ctl00_lblstdno_rptr">IS 9999 : 2000</span>
            </body>
        </html>
        """
        mock_get.return_value = mock_get_response

        from scripts.acquire_standards_metadata import process_standard
        record = process_standard("IS 15750")
        assert record['acquisition']['status'] == 'VALIDATION_FAILED'
