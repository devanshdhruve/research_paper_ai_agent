import os
import argparse
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import from your modules
from models.gemini_client import GeminiClient
from extractors.text_extractor import extract_text_from_pdf
from extractors.citation_extractor import extract_citations_from_references
from processors.summarizer import get_multimodal_summary_from_gemini
from processors.section_processor import get_section_from_gemini
from generators.pdf_generator import save_analysis_to_pdf

# NEW: Import memory components
from memory.vector_db import ResearchMemory
from utils.text_chunker import chunk_text, extract_paper_metadata

def main():
    """
    The main function for the MULTIMODAL AI research agent.
    """
    # Configure API key
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: Gemini API key not found.")
        return
    
    # Initialize Gemini client
    gemini_client = GeminiClient()
    print("✅ Gemini API key configured successfully!")

    # Argument parser
    parser = argparse.ArgumentParser(description="AI Research Paper Agent")
    parser.add_argument("--section", type=str, default="summary",
                        help="What to extract: summary | methodology | equation | citations | future_scope")
    parser.add_argument("--pdf", type=str, required=True,
                        help="Path to input PDF")
    args = parser.parse_args()

    input_pdf_path = args.pdf

    # Extract text
    extracted_text = extract_text_from_pdf(input_pdf_path)
    if not extracted_text:
        print("Ending process due to text extraction failure.")
        return
    
    # NEW: Initialize memory and store chunks
    memory = ResearchMemory()

    metadata = extract_paper_metadata(extracted_text)
    metadata.update({
        "file_path": input_pdf_path,
        "section_processed": [args.section]
    })

    chunks = chunk_text(extracted_text)
    paper_id = memory.store_chunks(extracted_text, chunks, metadata)

    print(f"📚 Paper stored in memory with ID: {paper_id}")

     # NEW: Search for similar papers before processing
    if args.section == "summary":
        similar_papers = memory.search_similar_papers(extracted_text[:500], n_results=3)
        if similar_papers:
            print(f"🔍 Found {len(similar_papers)} similar papers in memory")

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
                print(f"{i}. {c['text']}")  # Fixed: changed 'reference' to 'text'
                print(f"   ➡️ {c['link']}\n")

    elif args.section == "future_scope":
        section_text = get_section_from_gemini(input_pdf_path, extracted_text, "future_scope", gemini_client)
        if not section_text:
            return
        output_pdf_name = f"{file_name_without_ext}_future_scope.pdf"
        save_analysis_to_pdf(section_text, output_pdf_name, content_type='summary')

    else:
        print("❌ Unknown section. Use one of: summary | methodology | equation | citations | future_scope")
        return

if __name__ == "__main__":
    main()