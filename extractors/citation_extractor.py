import re
import requests
from extractors.text_extractor import extract_text_from_pdf

def extract_citations_from_references(pdf_path):
    """
    Extract citations from the References section by detecting
    patterns like 'Author, A. Author. YEAR. Title...'.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return []
    
    match = re.search(r"(references|bibliography)(.*)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        print("⚠️ Could not find References section.")
        return []
    
    refs_text = match.group(2)
    
    raw_refs = re.split(r"(?=\n?[A-Z][a-zA-Z\-\']+.*\d{4}\.)", refs_text)
    
    references = []
    for ref in raw_refs:
        ref = ref.strip().replace("\n", " ")
        if len(ref) > 50 and re.search(r"\d{4}", ref):
            references.append(ref)
    
    print(f"📚 Grouped into {len(references)} citations.")
    
    enriched = []
    for ref in references:
        print(f"🔍 Processing citation: {ref[:80]}...")
        doi, url = lookup_doi(ref)
        if doi:
            enriched.append({
                "reference": ref,
                "link": f"https://doi.org/{doi}"
            })
        else:
            enriched.append({
                "reference": ref,
                "link": f"https://scholar.google.com/scholar?q={ref.replace(' ', '+')}"
            })
    
    return enriched

def lookup_doi(reference_text):
    """
    Try to fetch DOI from CrossRef API.
    """
    try:
        headers = {"User-Agent": "ResearchAgent/1.0"}
        url = f"https://api.crossref.org/works?query.bibliographic={reference_text}&rows=1"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        if data.get("message", {}).get("items"):
            item = data["message"]["items"][0]
            doi = item.get("DOI")
            link = f"https://doi.org/{doi}" if doi else None
            return doi, link
    except Exception as e:
        print("⚠️ DOI lookup failed:", e)
    
    return None, None