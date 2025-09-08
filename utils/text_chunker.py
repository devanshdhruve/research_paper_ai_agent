import re
from typing import List, Dict
from datetime import datetime

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better embedding
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        
        # Break early if we're at the end
        if i + chunk_size >= len(words):
            break
    
    return chunks

def extract_paper_metadata(text: str) -> Dict:
    """
    Extract basic metadata from research paper text
    """
    metadata = {
        "title": "Unknown Title",
        "authors": "Unknown Authors", 
        "year": "Unknown Year",
        "processed_date": datetime.now().isoformat()
    }
    
    # Improved title extraction
    lines = text.split('\n')
    
    # Look for title patterns (usually early in document, centered, etc.)
    for i, line in enumerate(lines[:50]):  # Check first 50 lines
        line = line.strip()
        
        # Skip empty lines, page numbers, headers/footers
        if not line or len(line) < 10 or len(line) > 200:
            continue
            
        # Look for title-like lines (not ALL CAPS, not containing certain words)
        if (line[0].isupper() and  # Starts with capital
            not line.isupper() and  # Not all caps
            not any(word in line.lower() for word in [
                'abstract', 'introduction', 'figure', 'table', 'section',
                'journal', 'vol', 'pp', 'copyright', 'http'
            ]) and
            not line.endswith(('.', ',', ';')) and  # Doesn't end with punctuation
            not any(char.isdigit() for char in line)  # Doesn't contain numbers
        ):
            metadata["title"] = line
            break
    
    # Author extraction (look for common patterns)
    author_patterns = [
        r'([A-Z][a-z]+ [A-Z][a-z]+(?:, [A-Z][a-z]+ [A-Z][a-z]+)*)',
        r'([A-Z]\. [A-Z][a-z]+(?:, [A-Z]\. [A-Z][a-z]+)*)',
        r'([A-Z][a-z]+, [A-Z]\.(?:, [A-Z][a-z]+, [A-Z]\.)*)'
    ]
    
    for pattern in author_patterns:
        match = re.search(pattern, text[:2000])
        if match:
            metadata["authors"] = match.group(1)
            break
    
    # Year extraction
    year_match = re.search(r'\b(19|20)\d{2}\b', text[:3000])
    if year_match:
        metadata["year"] = year_match.group(0)
    
    return metadata