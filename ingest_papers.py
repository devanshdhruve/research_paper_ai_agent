import os
import glob
import argparse
from datetime import datetime
from memory.vector_db import ResearchMemory
from extractors.text_extractor import extract_text_from_pdf
from utils.text_chunker import chunk_text, extract_paper_metadata

def ingest_pdfs(pdf_paths):
    """Ingest multiple PDF files into memory"""
    memory = ResearchMemory()
    results = []
    
    for pdf_path in pdf_paths:
        try:
            if not os.path.exists(pdf_path):
                print(f"❌ File not found: {pdf_path}")
                results.append({"success": False, "error": "File not found", "path": pdf_path})
                continue
            
            print(f"📥 Ingesting: {os.path.basename(pdf_path)}...")
            
            # Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text:
                error_msg = "Text extraction failed"
                print(f"   ❌ {error_msg}")
                results.append({"success": False, "error": error_msg, "path": pdf_path})
                continue
            
            # Extract metadata
            metadata = extract_paper_metadata(text)
            metadata.update({
                "file_path": os.path.abspath(pdf_path),
                "file_name": os.path.basename(pdf_path),
                "file_size": os.path.getsize(pdf_path),
                "ingestion_date": datetime.now().isoformat(),
                "processed": False
            })
            
            # Chunk and store
            chunks = chunk_text(text)
            paper_id = memory.store_paper(text, metadata, chunks)
            
            print(f"   ✅ Success! ID: {paper_id}, Chunks: {len(chunks)}")
            print(f"   📝 Title: {metadata.get('title', 'Unknown')}")
            
            results.append({
                "success": True, 
                "paper_id": paper_id, 
                "path": pdf_path,
                "title": metadata.get("title", "Unknown"),
                "authors": metadata.get("authors", "Unknown"),
                "chunks": len(chunks)
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({"success": False, "error": str(e), "path": pdf_path})
    
    return results

def ingest_folder(folder_path, pattern="*.pdf"):
    """Ingest all PDFs from a folder"""
    pdf_files = glob.glob(os.path.join(folder_path, pattern))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {folder_path}")
        return []
    
    print(f"📚 Found {len(pdf_files)} PDF files in {folder_path}")
    return ingest_pdfs(pdf_files)

def main():
    parser = argparse.ArgumentParser(description="Ingest PDFs into research memory")
    parser.add_argument("--folder", "-f", default=".", 
                       help="Folder path (default: current directory)")
    parser.add_argument("--pattern", "-p", default="*.pdf", 
                       help="File pattern (default: *.pdf)")
    parser.add_argument("--output", "-o", 
                       help="Output report file (optional)")
    
    args = parser.parse_args()
    
    # Ingest papers
    results = ingest_folder(args.folder, args.pattern)
    
    # Print summary
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    print(f"\n{'='*50}")
    print(f"🎉 INGESTION COMPLETE!")
    print(f"{'='*50}")
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}")
    
    if success_count > 0:
        print(f"\n📊 Successful papers:")
        for result in results:
            if result["success"]:
                print(f"   • {result['title']} ({result['paper_id']})")
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("PDF Ingestion Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Folder: {os.path.abspath(args.folder)}\n")
            f.write(f"Total files: {total_count}\n")
            f.write(f"Successful: {success_count}\n")
            f.write(f"Failed: {total_count - success_count}\n\n")
            
            f.write("DETAILED RESULTS:\n")
            f.write("-" * 50 + "\n")
            for result in results:
                status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
                f.write(f"{status}: {result['path']}\n")
                if result["success"]:
                    f.write(f"     Paper ID: {result['paper_id']}\n")
                    f.write(f"     Title: {result['title']}\n")
                else:
                    f.write(f"     Error: {result['error']}\n")
                f.write("\n")
        
        print(f"\n📄 Report saved to: {args.output}")

if __name__ == "__main__":
    main()