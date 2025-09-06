import os
import argparse
import google.generativeai as genai
from dotenv import load_dotenv
from agent_utils import (
    extract_text_from_pdf,
    get_multimodal_summary_from_gemini,
    get_section_from_gemini,
    extract_citations_from_references,
    # --- UPDATED IMPORT ---
    # The old save_summary_to_pdf is now replaced by the new unified function.
    save_analysis_to_pdf, 
)


def main():
    """
    The main function for the MULTIMODAL AI research agent.
    """
    # --- 1. CONFIGURE API KEY ---
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌  Error: Gemini API key not found.")
        return
    genai.configure(api_key=api_key)
    print("✅  Gemini API key configured successfully!")

    # --- 2. ARGUMENT PARSER ---
    parser = argparse.ArgumentParser(description="AI Research Paper Agent")
    # Added 'equation' to the help string for clarity
    parser.add_argument("--section", type=str, default="summary",
                        help="What to extract: summary | methodology | equation | citations | future_scope")
    parser.add_argument("--pdf", type=str, required=True,
                        help="Path to input PDF")
    args = parser.parse_args()

    input_pdf_path = args.pdf

    # --- 3. EXTRACT TEXT ---
    extracted_text = extract_text_from_pdf(input_pdf_path)
    if not extracted_text:
        print("Ending process due to text extraction failure.")
        return

    # --- 4. RUN SELECTED MODE ---
    base_name = os.path.basename(input_pdf_path)
    file_name_without_ext = os.path.splitext(base_name)[0]

    # --- Full Multimodal Summary ---
    if args.section == "summary":
        summary = get_multimodal_summary_from_gemini(input_pdf_path, extracted_text)
        if not summary:
            print("Ending process due to summary generation failure.")
            return
        output_pdf_name = f"{file_name_without_ext}_summary.pdf"
        # UPDATED CALL: Using the new function with 'summary' mode.
        save_analysis_to_pdf(summary, output_pdf_name, content_type='summary')

    # --- Methodology Section ---
    elif args.section == "methodology":
        section_text = get_section_from_gemini(input_pdf_path, extracted_text, section="methodology")
        if not section_text: return
        output_pdf_name = f"{file_name_without_ext}_methodology.pdf"
        # UPDATED CALL: Using the new function with 'summary' mode.
        save_analysis_to_pdf(section_text, output_pdf_name, content_type='summary')

    # --- Equation Analysis ---
    # CORRECTED: This now accepts both 'equation' and 'equations' from the command line.
    elif args.section in ["equation", "equations"]:
        # UPDATED LOGIC: Now we get the full analysis from Gemini first.
        # We pass the singular 'equation' because that's the key in the agent_utils dictionary.
        section_text = get_section_from_gemini(input_pdf_path, extracted_text, section="equations")
        if not section_text: return
        output_pdf_name = f"{file_name_without_ext}_equation_analysis.pdf"
        # UPDATED CALL: Using the new function with 'equations' mode.
        save_analysis_to_pdf(section_text, output_pdf_name, content_type='equations')

    # --- Citations ---
    elif args.section == "citations":
        citations = extract_citations_from_references(input_pdf_path)
        if not citations:
            print("\n⚠️ No citations found.")
        else:
            print(f"\n📚 Extracted {len(citations)} Citations with Links:\n")
            for i, c in enumerate(citations, 1):
                print(f"{i}. {c['reference']}")
                print(f"   ➡️ {c['link']}\n")

    # --- Future Scope ---
    elif args.section == "future_scope":
        section_text = get_section_from_gemini(input_pdf_path, extracted_text, section="future_scope")
        if not section_text: return
        output_pdf_name = f"{file_name_without_ext}_future_scope.pdf"
        # UPDATED CALL: Using the new function with 'summary' mode.
        save_analysis_to_pdf(section_text, output_pdf_name, content_type='summary')

    else:
        print("❌ Unknown section. Use one of: summary | methodology | equation | citations | future_scope")
        return


if __name__ == "__main__":
    main()

