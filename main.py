import os
import argparse
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.gemini_client import GeminiClient
from extractors.text_extractor import extract_text_from_pdf
from extractors.citation_extractor import extract_citations_from_references
from processors.summarizer import get_multimodal_summary_from_gemini
from processors.section_processor import get_section_from_gemini
from generators.pdf_generator import save_analysis_to_pdf

from datetime import datetime   

# Memory components
from memory.vector_db import ResearchMemory
from utils.text_chunker import chunk_text, extract_paper_metadata

def process_stored_paper(paper_id, section, gemini_client, memory):
    """Process a paper that's already stored in memory"""
    # Retrieve paper from memory
    paper_data = memory.get_paper_by_id(paper_id)
    if not paper_data:
        print(f"❌ Paper {paper_id} not found in memory")
        return None
    
    print(f"📖 Processing: {paper_data['metadata'].get('title', 'Unknown')}")
    
    # Get the actual PDF path for multimodal processing
    pdf_path = paper_data['metadata']['file_path']
    
    # Process based on requested section
    if section == "summary":
        # For multimodal processing, we still need the PDF file
        result = get_multimodal_summary_from_gemini(
            pdf_path, paper_data['content'], gemini_client
        )
    elif section == "citations":
        result = extract_citations_from_references(pdf_path)
    else:
        result = get_section_from_gemini(
            pdf_path, paper_data['content'], section, gemini_client
        )
    
    # Update metadata to mark as processed
    memory.update_paper_metadata(paper_id, {
        "processed": True,
        f"processed_{section}": datetime.now().isoformat()
    })
    
    return result

def list_available_papers(memory):
    """List all papers available in memory"""
    papers = memory.get_all_papers()
    print("\n📚 Papers in Memory:")
    print("====================")
    for i, paper_id in enumerate(papers, 1):
        paper_data = memory.get_paper_by_id(paper_id)
        if paper_data:
            title = paper_data['metadata'].get('title', 'Unknown')
            processed = "✅" if paper_data['metadata'].get('processed') else "⏳"
            print(f"{i}. {processed} {title} ({paper_id})")

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: Gemini API key not found.")
        return
    
    gemini_client = GeminiClient()
    memory = ResearchMemory()
    
    parser = argparse.ArgumentParser(description="AI Research Paper Agent")
    parser.add_argument("--section", type=str, default="summary",
                        help="summary | methodology | equation | citations | future_scope")
    parser.add_argument("--pdf", type=str, help="Path to new PDF file")
    parser.add_argument("--paper-id", type=str, help="Process paper from memory")
    parser.add_argument("--list", action="store_true", help="List papers in memory")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_papers(memory)
        return
    
    if args.paper_id:
        # Process paper from memory
        result = process_stored_paper(args.paper_id, args.section, gemini_client, memory)
        if result:
            # Save or display results
            if args.section == "citations":
                print(f"\n📚 Citations found: {len(result)}")
                for i, citation in enumerate(result, 1):
                    print(f"{i}. {citation['text']}")
                    print(f"   🔗 {citation['link']}")
            else:
                output_name = f"{args.paper_id}_{args.section}.pdf"
                save_analysis_to_pdf(result, output_name, content_type=args.section)
        return
    
    if args.pdf:
        # Process new PDF (your existing functionality)
        # ... [your existing code for new PDF processing] ...
        pass
    else:
        print("❌ Please specify either --pdf or --paper-id")
        return

if __name__ == "__main__":
    main()