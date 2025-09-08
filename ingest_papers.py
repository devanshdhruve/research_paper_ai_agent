import os
import glob
import argparse
from memory.vector_db import ResearchMemory
from extractors.text_extractor import extract_text_from_pdf
from utils.text_chunker import chunk_text, extract_paper_metadata

from datetime import datetime

def ingest_papers(pdf_paths, skip_errors=True):
    """
    Bulk ingest PDFs into ChromaDB without processing
    Returns: List of (paper_id, success_status)
    """
    memory = ResearchMemory()
    results = []
    
    for pdf_path in pdf_paths:
        try:
            print(f"📥 Ingesting: {os.path.basename(pdf_path)}...")
            
            # Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text:
                print(f"   ❌ Failed to extract text")
                results.append((pdf_path, False, "Text extraction failed"))
                continue
            
            # Extract metadata
            metadata = extract_paper_metadata(text)
            metadata.update({
                "file_path": os.path.abspath(pdf_path),
                "file_name": os.path.basename(pdf_path),
                "ingestion_date": datetime.now().isoformat(),
                "processed": False  # Mark as not processed yet
            })
            
            # Chunk and store
            chunks = chunk_text(text)
            paper_id = memory.store_paper(text, metadata, chunks)
            
            print(f"   ✅ Success! ID: {paper_id}, Chunks: {len(chunks)}")
            results.append((pdf_path, True, paper_id))
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((pdf_path, False, str(e)))
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Bulk ingest PDFs into memory")
    parser.add_argument("--input", "-i", nargs="+", help="PDF files or directories")
    parser.add_argument("--output", "-o", help="Output report file")
    
    args = parser.parse_args()
    
    # Collect PDF paths
    pdf_paths = []
    if args.input:
        for input_path in args.input:
            if os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
                pdf_paths.append(input_path)
            elif os.path.isdir(input_path):
                pdf_paths.extend(glob.glob(os.path.join(input_path, "*.pdf")))
    
    if not pdf_paths:
        pdf_paths = glob.glob("*.pdf")
    
    if not pdf_paths:
        print("❌ No PDF files found!")
        return
    
    print(f"📚 Found {len(pdf_paths)} PDF files for ingestion...")
    
    # Ingest all papers
    results = ingest_papers(pdf_paths)
    
    # Generate report
    success_count = sum(1 for _, success, _ in results if success)
    
    print(f"\n🎉 Ingestion Complete!")
    print(f"   Successful: {success_count}/{len(pdf_paths)}")
    print(f"   Failed: {len(pdf_paths) - success_count}")
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write("PDF Ingestion Report\n")
            f.write("====================\n\n")
            for pdf_path, success, message in results:
                status = "✅ SUCCESS" if success else "❌ FAILED"
                f.write(f"{status}: {pdf_path} - {message}\n")

if __name__ == "__main__":
    main()