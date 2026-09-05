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
    if "jeweller" in url_lower or "jeweller" in text_lower:
        return "JEWELLER_REGISTRATION"
    if "huid" in url_lower or "huid" in text_lower:
        return "HUID"
    if "centre" in url_lower or "ahc" in text_lower:
        return "AHC"
    if "fee" in url_lower or "charges" in text_lower:
        return "FEES"
    return "GENERAL_PROCEDURE"
