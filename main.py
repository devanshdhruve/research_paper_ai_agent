import os
import argparse
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import from your modules
from models.gemini_client import GeminiClient
from extractors.text_extractor import extract_text_from_pdf
from extractors.citation_extractor import extract_citations_from_references
from processors.summarizer import get_multimodal_summary_from_gemini
from processors.section_processor import get_section_from_gemini
from generators.pdf_generator import save_analysis_to_pdf

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
    
    # Check if we have the original PDF path for multimodal processing
    pdf_path = paper_data['metadata'].get('file_path')
    
    if not pdf_path or not os.path.exists(pdf_path):
        print("⚠️ Original PDF not found, using text-only processing")
        # Fallback to text-only processing
        if section == "summary":
            result = get_multimodal_summary_from_gemini(
                None, paper_data['content'], gemini_client, text_only=True
            )
        elif section == "citations":
            # For citations, we need the PDF, so we can't process without it
            print("❌ Citations extraction requires original PDF file")
            return None
        else:
            result = get_section_from_gemini(
                None, paper_data['content'], section, gemini_client, text_only=True
            )
    else:
        # Process with original PDF for multimodal
        if section == "summary":
            result = get_multimodal_summary_from_gemini(
                pdf_path, paper_data['content'], gemini_client
            )
        elif section == "citations":
            result = extract_citations_from_references(pdf_path)
        else:
            result = get_section_from_gemini(
                pdf_path, paper_data['content'], section, gemini_client
            )
    
    # Update metadata to mark as processed (if method exists)
    if hasattr(memory, 'update_paper_metadata'):
        memory.update_paper_metadata(paper_id, {
            "processed": True,
            f"processed_{section}": datetime.now().isoformat()
        })
    else:
        print("ℹ️ Paper processed (metadata update not available)")
    
    return result

def list_available_papers(memory, show_numbers=False):
    """List all papers in the database"""
    print("\n📚 Papers in Memory:")
    print("====================")
    
    papers_metadata = memory.get_all_paper_metadata()
    
    if not papers_metadata:
        print("No papers found in the database.")
        return []
    
    for i, metadata in enumerate(papers_metadata, 1):
        if show_numbers:
            print(f"\n{i}. {metadata.get('title', 'Untitled')}")
        else:
            print(f"\n- {metadata.get('title', 'Untitled')}")
        print(f"   Authors: {metadata.get('authors', 'Unknown')}")
        print(f"   ID: {metadata.get('paper_id', 'Unknown')}")
        print(f"   Source: {metadata.get('source', 'Unknown')}")
        
        # Show processing status if available
        if metadata.get('processed'):
            processed_sections = [key.replace('processed_', '') for key in metadata.keys() 
                                if key.startswith('processed_') and metadata[key]]
            if processed_sections:
                print(f"   ✅ Processed sections: {', '.join(processed_sections)}")
    
    return papers_metadata

def select_paper_interactively(memory):
    """Let user select a paper by number"""
    papers_metadata = list_available_papers(memory, show_numbers=True)
    
    if not papers_metadata:
        return None
    
    try:
        choice = input(f"\n🎯 Select a paper (1-{len(papers_metadata)}), or 'q' to quit: ")
        if choice.lower() == 'q':
            return None
        
        paper_index = int(choice) - 1
        if 0 <= paper_index < len(papers_metadata):
            selected_paper = papers_metadata[paper_index]
            print(f"✅ Selected: {selected_paper.get('title', 'Unknown')}")
            return selected_paper.get('paper_id')
        else:
            print("❌ Invalid selection")
            return None
            
    except ValueError:
        print("❌ Please enter a valid number")
        return None

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
                        help="summary | methodology | equation | citations | future_scope | literature_survey")
    parser.add_argument("--pdf", type=str, help="Path to new PDF file")
    parser.add_argument("--paper-id", type=str, help="Process paper from memory (use --select for interactive)")
    parser.add_argument("--select", action="store_true", help="Select paper interactively from list")
    parser.add_argument("--list", action="store_true", help="List papers in memory")
    parser.add_argument("--all", action="store_true", help="Process all papers in memory for the given section")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_papers(memory)
        return
    
    # Handle paper selection
    paper_id = None
    if args.select:
        paper_id = select_paper_interactively(memory)
        if not paper_id:
            return
    elif args.paper_id:
        paper_id = args.paper_id
    
    if args.all:
        # Process all papers in memory
        papers_metadata = memory.get_all_paper_metadata()
        if not papers_metadata:
            print("❌ No papers found in memory to process")
            return
        
        print(f"🔍 Processing {len(papers_metadata)} papers for section: {args.section}")
        for paper_metadata in papers_metadata:
            paper_id = paper_metadata.get('paper_id')
            if paper_id:
                print(f"\n📄 Processing paper: {paper_metadata.get('title', 'Unknown')}")
                result = process_stored_paper(paper_id, args.section, gemini_client, memory)
                if result:
                    output_name = f"{paper_id}_{args.section}.pdf"
                    save_analysis_to_pdf(result, output_name, content_type=args.section)
                    print(f"✅ Saved: {output_name}")
        return
    
    if paper_id:
        # Process paper from memory
        result = process_stored_paper(paper_id, args.section, gemini_client, memory)
        if result:
            # Save or display results
            if args.section == "citations":
                print(f"\n📚 Citations found: {len(result)}")
                for i, citation in enumerate(result, 1):
                    print(f"{i}. {citation['text']}")
                    print(f"   🔗 {citation['link']}")
            else:
                # Get paper title for better output naming
                paper_data = memory.get_paper_by_id(paper_id)
                paper_title = paper_data['metadata'].get('title', paper_id) if paper_data else paper_id
                # Clean title for filename
                clean_title = "".join(c for c in paper_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                clean_title = clean_title.replace(' ', '_')[:50]  # Limit length and replace spaces
                
                output_name = f"{clean_title}_{args.section}.pdf"
                save_analysis_to_pdf(result, output_name, content_type=args.section)
                print(f"✅ Analysis saved to: {output_name}")
        return
    
    if args.pdf:
        # Process new PDF file
        input_pdf_path = args.pdf
        
        if not os.path.exists(input_pdf_path):
            print(f"❌ PDF file not found: {input_pdf_path}")
            return

        # Extract text
        print(f"📄 Processing new PDF: {os.path.basename(input_pdf_path)}")
        extracted_text = extract_text_from_pdf(input_pdf_path)
        if not extracted_text:
            print("Ending process due to text extraction failure.")
            return

        # Also store in memory while processing
        metadata = extract_paper_metadata(extracted_text)
        metadata.update({
            "file_path": os.path.abspath(input_pdf_path),
            "file_name": os.path.basename(input_pdf_path),
            "section_processed": [args.section]
        })

        chunks = chunk_text(extracted_text)
        paper_id = memory.store_paper(extracted_text, metadata, chunks)
        print(f"📚 Also stored in memory with ID: {paper_id}")

        # Run selected mode
        base_name = os.path.basename(input_pdf_path)
        file_name_without_ext = os.path.splitext(base_name)[0]

        if args.section == "summary":
            summary = get_multimodal_summary_from_gemini(input_pdf_path, extracted_text, gemini_client)
            if not summary:
                print("Ending process due to summary generation failure.")
                return
            output_pdf_name = f"{file_name_without_ext}_summary.pdf"
            save_analysis_to_pdf(summary, output_pdf_name, content_type='summary')

        elif args.section == "methodology":
            section_text = get_section_from_gemini(input_pdf_path, extracted_text, "methodology", gemini_client)
            if not section_text:
                return
            output_pdf_name = f"{file_name_without_ext}_methodology.pdf"
            save_analysis_to_pdf(section_text, output_pdf_name, content_type='summary')

        elif args.section in ["equation", "equations"]:
            section_text = get_section_from_gemini(input_pdf_path, extracted_text, "equations", gemini_client)
            if not section_text:
                return
            output_pdf_name = f"{file_name_without_ext}_equation_analysis.pdf"
            save_analysis_to_pdf(section_text, output_pdf_name, content_type='equations')

        elif args.section == "citations":
            citations = extract_citations_from_references(input_pdf_path)
            if not citations:
                print("\n⚠️ No citations found.")
            else:
                print(f"\n📚 Extracted {len(citations)} Citations with Links:\n")
                for i, c in enumerate(citations, 1):
                    print(f"{i}. {c['text']}")
                    print(f"   ➡️ {c['link']}")

        elif args.section == "future_scope":
            section_text = get_section_from_gemini(input_pdf_path, extracted_text, "future_scope", gemini_client)
            if not section_text:
                return
            output_pdf_name = f"{file_name_without_ext}_future_scope.pdf"
            save_analysis_to_pdf(section_text, output_pdf_name, content_type='summary')

        elif args.section == "literature_survey":
            section_text = get_section_from_gemini(input_pdf_path, extracted_text, "literature_survey", gemini_client)
            if not section_text:
                return
            output_pdf_name = f"{file_name_without_ext}_literature_survey.pdf"
            save_analysis_to_pdf(section_text, output_pdf_name, content_type='summary')

        else:
            print("❌ Unknown section. Use one of: summary | methodology | equation | citations | future_scope | literature_survey")
            return
    
    else:
        print("❌ Please specify either --pdf, --paper-id, or --select")
        print("   Usage examples:")
        print("   - Process new PDF: python main.py --pdf paper.pdf --section summary")
        print("   - Process with paper ID: python main.py --paper-id YOUR_PAPER_ID --section methodology")
        print("   - Select paper interactively: python main.py --select --section summary")
        print("   - List papers: python main.py --list")
        print("   - Process all papers: python main.py --all --section summary")
        return

if __name__ == "__main__":
    main()