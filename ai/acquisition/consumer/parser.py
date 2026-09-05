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
    if "complaint" in url_lower or "grievance" in text_lower:
        return "COMPLAINT_MECHANISM"
    if "verify" in url_lower or "verification" in text_lower or "bis care" in text_lower:
        return "VERIFICATION"
    if "awareness" in url_lower or "consumer" in text_lower:
        return "AWARENESS"
    if "faq" in url_lower or "frequently" in text_lower:
        return "FAQ"
    if "contact" in url_lower or "helpdesk" in url_lower or "helpdesk" in text_lower:
        return "CONTACT"
    return "AWARENESS"
