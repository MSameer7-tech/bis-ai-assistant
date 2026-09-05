import io
from bs4 import BeautifulSoup

def extract_text_from_pdf(pdf_bytes):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text, "SUCCESS"
    except Exception as e:
        return str(e), "FAILED"

def extract_text_from_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True), "SUCCESS"
    except Exception as e:
        return str(e), "FAILED"

def infer_information_type(url, text):
    url_lower = url.lower()
    text_lower = text.lower()
    if "crs" in url_lower or "compulsory" in text_lower:
        return "CRS"
    if "fmcs" in url_lower or "foreign" in text_lower or "fmcs" in text_lower:
        return "FMCS"
    if "fee" in url_lower or "charges" in text_lower:
        return "FEES"
    if "faq" in url_lower or "frequently" in text_lower:
        return "FAQ"
    if "scheme" in url_lower or "scheme" in text_lower:
        return "SCHEME_INFO"
    return "APPLICATION_PROCEDURE"
