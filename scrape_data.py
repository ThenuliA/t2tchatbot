import io
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


def is_pdf_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith('.pdf')


def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", " ", text)

    lines = []
    for line in text.splitlines():
        normalized = re.sub(r"\s+", " ", line).strip()
        if normalized:
            lines.append(normalized)

    return "\n".join(lines)


def extract_pdf_text_from_bytes(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_text = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        cleaned_page_text = clean_extracted_text(page_text)
        if cleaned_page_text:
            pages_text.append(cleaned_page_text)

    return "\n\n".join(pages_text)


def get_deep_website_data(base_url):
    all_text = []
    visited_urls = set()
    
    try:
        # 1. Scrape the Main Page
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main page text
        main_text = clean_soup_text(soup)
        all_text.append(f"--- MAIN PAGE ---\n{main_text}")
        visited_urls.add(base_url)

        # 2. Find "Show Details" or "Explore" links
        links = soup.find_all('a', href=True)
        program_keywords = ['crisp', 'ifap', 'program', 'details', 'event']
        
        for link in links:
            href = link['href']
            full_url = urljoin(base_url, href)

            if full_url in visited_urls:
                continue

            if is_pdf_url(full_url):
                print(f"Reading PDF from: {full_url}...")
                try:
                    pdf_response = requests.get(full_url, timeout=12)
                    pdf_response.raise_for_status()

                    pdf_text = extract_pdf_text_from_bytes(pdf_response.content)
                    if pdf_text:
                        all_text.append(f"\n--- PDF FROM {full_url} ---\n{pdf_text}")
                        print(f"Successfully extracted {len(pdf_text)} characters from PDF")
                    else:
                        print(f"No readable text extracted from PDF: {full_url}")

                    visited_urls.add(full_url)
                except Exception as e:
                    print(f"Error reading PDF {full_url}: {e}")
                continue
            
            # Only visit internal links that seem relevant and HAVEN'T BEEN VISITED
            if base_url in full_url:
                if any(key in full_url.lower() for key in program_keywords):
                    print(f"Scraping details from: {full_url}...")
                    try:
                        sub_res = requests.get(full_url, timeout=8)
                        sub_res.raise_for_status()

                        content_type = sub_res.headers.get("Content-Type", "").lower()
                        if "application/pdf" in content_type:
                            pdf_text = extract_pdf_text_from_bytes(sub_res.content)
                            if pdf_text:
                                all_text.append(f"\n--- PDF FROM {full_url} ---\n{pdf_text}")
                                print(f"Successfully extracted {len(pdf_text)} characters from PDF")
                            else:
                                print(f"No readable text extracted from PDF: {full_url}")
                        else:
                            sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                            details_text = clean_soup_text(sub_soup)
                            if details_text:
                                all_text.append(f"\n--- DETAILS FROM {full_url} ---\n{details_text}")

                        visited_urls.add(full_url)
                    except Exception as e:
                        print(f"Error scraping {full_url}: {e}")
                        continue
                        
        return "\n".join(all_text)
    except Exception as e:
        return f"Error scraping: {e}"


def clean_soup_text(soup):
    for script_or_style in soup(["script", "style", "footer", "nav"]):
        script_or_style.extract()
    text = soup.get_text(separator="\n")
    return clean_extracted_text(text)