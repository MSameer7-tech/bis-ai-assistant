import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class LicencesDiscovery:
    def __init__(self, start_urls):
        self.start_urls = start_urls
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; BIS-Licences-Acquisition/1.0)"}

    def fetch(self, url, timeout=10):
        try:
            r = requests.get(url, headers=self.headers, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            return None

    def discover_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a['href']
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            # Prioritize BIS official domains and subdomains
            if "bis.gov.in" in parsed.netloc or "crsbis.in" in parsed.netloc or "manakonline.in" in parsed.netloc:
                if full_url not in links:
                    links.append(full_url)
        return links

    def categorize_link(self, url):
        url_lower = url.lower()
        if url_lower.endswith(".pdf"):
            return "PDF"
        return "HTML"
