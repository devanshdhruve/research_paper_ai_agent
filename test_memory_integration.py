import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.vector_db import ResearchMemory
from extractors.text_extractor import extract_text_from_pdf
from utils.text_chunker import chunk_text, extract_paper_metadata

def test_memory():
    """Test the memory system with a real PDF"""
    print("🧠 Testing Memory Integration...")
    
    # Initialize memory
    memory = ResearchMemory()
    print("✅ Memory system initialized")
    
    # Test with a PDF
    pdf_path = "2508.07090v1.pdf"  # Your test PDF
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found")
        return
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("❌ Text extraction failed")
        return
    
    print(f"✅ Extracted {len(text)} characters")
    
    # Extract metadata and chunk
    metadata = extract_paper_metadata(text)
    metadata["file_path"] = pdf_path
    chunks = chunk_text(text)
    
    print(f"✅ Created {len(chunks)} chunks")
    print(f"📋 Metadata: {metadata['title']}")
    
    # Store in memory
    paper_id = memory.store_paper(text, metadata, chunks)
    print(f"✅ Paper stored with ID: {paper_id}")
    
    # Test search
    search_query = "machine learning"  # Try different queries
    results = memory.search_similar_papers(search_query, 3)
    print(f"✅ Search found {len(results)} similar papers")
    
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['metadata'].get('title', 'No title')} (score: {result['similarity']:.3f})")
    
    print("🎉 Memory integration test completed successfully!")

if __name__ == "__main__":
    test_memory()