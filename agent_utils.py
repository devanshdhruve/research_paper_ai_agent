import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF
import fitz
import pytesseract
from PIL import Image
import io
import re
import requests
import matplotlib.pyplot as plt  # still here if you use it elsewhere

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, ListStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem, Image as ReportLabImage
)
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# NEW imports for LaTeX rendering
import katex          # render LaTeX → SVG
import cairosvg       # convert SVG → PNG


# This function is unchanged
def extract_text_from_pdf(pdf_path):
    print(f"Reading text from: {pdf_path}")
    # ... (code for text extraction remains the same)
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
        
        if not full_text:
            print("Warning: No text could be extracted from the PDF.")
            return None

        print("Text extracted successfully.")
        return full_text
    
    except Exception as e:
        print(f"An unexpected error occurred during text extraction: {e}")
        return None

# --- NEW FUNCTION TO EXTRACT IMAGES ---
def extract_images_and_captions(pdf_path, max_selected=7, manual=False):
    """
    Extract images + captions from PDF.
    Runs OCR on each image and selects the most important ones.
    Returns:
      - figures_text: combined OCR+caption text for ALL figures
      - selected_images: a list of Pillow Images for Gemini Vision
    """
    # --- START OF NEW PRINT STATEMENT ---
    print(f"🖼️  Starting image and caption extraction from: {pdf_path}")
    # --- END OF NEW PRINT STATEMENT ---

    doc = fitz.open(pdf_path)
    figures_info = []
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            # Extract captions from page text (if any)
            page_text = page.get_text("text")
            captions = re.findall(r"(Figure\s?\d+[:.].*)", page_text, re.IGNORECASE)

            # loops through all images in the page, extracts each images as the raw bytes and opens it with PIL
            for img_index, img in enumerate(image_list, start=1):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))

                # OCR
                ocr_text = pytesseract.image_to_string(image)

                # Try to find a caption for this image
                caption = captions[img_index-1] if img_index-1 < len(captions) else "No caption found"

                # stores all useful info about this figure in a dicitonary
                figures_info.append({
                    "page": page_num + 1,
                    "caption": caption.strip(),
                    "ocr": ocr_text.strip(),
                    "image": image
                })

        # --- Auto-selection of important figures ---
        # Prioritize figures/tables with "Figure" or "Table" in the caption
        selected = [fig for fig in figures_info if fig["caption"].lower().startswith(("figure", "table"))]

        # If none found, look for keywords
        if not selected:
            keywords = ["accuracy", "result", "performance", "evaluation", "bias", "comparison", "ablation", "error", "score"]
            selected = [fig for fig in figures_info if any(k in fig["caption"].lower() for k in keywords)]

        # Final fallback: pick the first few figures
        if not selected:
            selected = figures_info[:max_selected]
        else:
            selected = selected[:max_selected]

        # --- Manual override if needed ---
        if manual: 
            print("\nAvailable figures:")
            for i, fig in enumerate(figures_info):
                print(f"{i+1}. Page {fig['page']} - Caption: {fig['caption']}...")
            chosen = input(f"Enter figure numbers to keep (comma-seperated, max {max_selected}): ")
            chosen_ids = [int(x.strip())-1 for x in chosen.split(",") if x.strip().isdigit()]
            selected = [figures_info[i] for i in chosen_ids if 0 <= i < len(figures_info)]

        # Build text block (all figures included here as text)
        figures_text = "\n\n".join(
            [f"[Figure on page {f['page']}] {f['caption']}\nOCR: {f['ocr']}" for f in figures_info]
        )

        # --- START OF NEW SUCCESS MESSAGE ---
        if figures_info:
            print(f"✅ Success! Found {len(figures_info)} total figures. Selected {len(selected)} for analysis.")
        else:
            print("⚠️  No images found in the PDF.")
        # --- END OF NEW SUCCESS MESSAGE ---

        return figures_text, [f["image"] for f in selected]

    except Exception as e:
        # --- START OF NEW ERROR MESSAGE ---
        print(f"❌ An error occurred during image extraction: {e}")
        # --- END OF NEW ERROR MESSAGE ---
        return "", [] # Return empty values on failure

# --- UPDATED FUNCTION FOR MULTIMODAL SUMMARIZATION ---
def get_multimodal_summary_from_gemini(pdf_path, text_content, model_choice="flash"):
    """
    Sends text + OCR captions + selected images to Gemini for summarization.
    """

    # Use Gemini 2.5 Flash
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Get figures info from updated extractor
    figures_text, selected_images = extract_images_and_captions(pdf_path, max_selected=5, manual=False)

    # Build the prompt
    prompt = f"""
    You are an expert research assistant. Analyze the following research paper thoroughly.
    Use the paper text, extracted figure captions, OCR text, and selected figure images
    to provide a clear, structured academic-style report.

    Do NOT just summarize — identify contributions, context, methods, gaps, and future work.
    Cross-check figures with text for consistency. If information is missing, explicitly state "Not mentioned".

    Please output in the following sections (use EXACT headings):

    ## Core Idea & Contribution
    - Central research question
    - Unique contribution compared to prior work

    ## Research Gap & Motivation
    - What prior work left unanswered
    - Why this problem matters in the broader research context

    ## Methodology
    - Datasets, models, or approaches
    - Experimental setup and evaluation metrics
    - Notes from diagrams/figures if relevant

    ## Key Findings & Results
    - Main findings
    - What charts/tables reveal (bias, comparisons, accuracy, etc.)
    - Highlight specific numbers if available

    ## Literature Context
    - Previous benchmarks/datasets cited
    - How this work extends or differs from them

    ## Limitations
    - Limitations acknowledged by authors
    - Any extra weaknesses you notice

    ## Avenues for Future Research
    - Concrete new directions
    - Improvements or extensions to overcome weaknesses

    ---
    FIGURES (OCR + captions):
    {figures_text}

    ---
    RESEARCH PAPER TEXT BEGINS:
    """

    # Build input for Gemini
    content = [prompt, text_content]
    content.extend(selected_images)  # Only selected images are added

    print("🧠 Sending text + figures to Gemini for summarization...")
    try:
        response = model.generate_content(content)
        print("✅ Summary generated successfully.")
        return response.text
    except Exception as e:
        print(f"❌ Error during Gemini API call: {e}")
        return None
    
# --- UPDATED UNIFIED FUNCTION TO SAVE ANY ANALYSIS TO PDF ---
def save_analysis_to_pdf(analysis_text, output_pdf_name, content_type='summary'):
    """
    Saves analysis text to a formatted PDF. 
    - 'summary': Formats text with headings and bullet points.
    - 'equations': Formats text with headings and renders LaTeX equations as images.
    """
    print(f"📄 Saving {content_type} analysis to {output_pdf_name}...")
    doc = SimpleDocTemplate(output_pdf_name, pagesize=A4,
                            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                   fontSize=14, spaceAfter=10, textColor=colors.darkblue)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'],
                                spaceAfter=6, leading=14, alignment=TA_LEFT)
    bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'],
                                  fontSize=11, leftIndent=20, spaceAfter=6)

    if content_type == 'summary':
        sections = analysis_text.split("## ")
        for section in sections:
            if not section.strip():
                continue
            lines = section.strip().splitlines()
            title = lines[0].strip()
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 6))
            content_lines = [l.strip("-• ") for l in lines[1:] if l.strip()]
            if content_lines:
                bullets = ListFlowable(
                    [ListItem(Paragraph(line, bullet_style)) for line in content_lines],
                    bulletType='bullet'
                )
                story.append(bullets)
            story.append(Spacer(1, 12))

    elif content_type == 'equations':
        # Clean up the text and split into sections
        cleaned_text = re.sub(r'--- PAGE \d+ ---', '', analysis_text).strip()
        sections = re.split(r'\s*---\s*', cleaned_text)
        
        for section in sections:
            if not section.strip():
                continue
            
            # Check if this section contains an equation
            equation_match = re.search(r"(.*?Equation:)\s*(\$\$.*?\$\$)\s*(.*)", section, re.DOTALL | re.IGNORECASE)
            
            if equation_match:
                # This section has an equation
                title_text = equation_match.group(1).replace('###', '').replace('**', '').strip()
                latex_string = re.sub(r'^\$\$|\$\$$', '', equation_match.group(2)).strip()
                explanation_text = equation_match.group(3).strip()

                # Add title
                story.append(Paragraph(title_text, heading_style))
                story.append(Spacer(1, 6))

                try:
                    # Render LaTeX to PNG using matplotlib as fallback
                    fig = plt.figure(figsize=(8, 2))
                    try:
                        # Try with LaTeX rendering
                        plt.text(0.5, 0.5, f"${latex_string}$", usetex=True,
                                 fontsize=14, va='center', ha='center')
                    except Exception:
                        # Fallback to MathText
                        plt.text(0.5, 0.5, f"${latex_string}$", usetex=False,
                                 fontsize=14, va='center', ha='center')
                    
                    plt.axis('off')
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.2, dpi=300)
                    plt.close(fig)
                    buf.seek(0)

                    # Add the rendered equation image
                    img = ReportLabImage(ImageReader(buf), hAlign='CENTER')
                    # Scale image to fit page width
                    max_width = 400
                    if img.imageWidth > max_width:
                        ratio = max_width / img.imageWidth
                        img.drawWidth = max_width
                        img.drawHeight = img.imageHeight * ratio
                    
                    story.append(img)
                    story.append(Spacer(1, 12))
                    
                except Exception as e:
                    print(f"⚠️ Could not render LaTeX: {latex_string}. Error: {e}")
                    # Fallback: show LaTeX code
                    story.append(Paragraph(f"<i>LaTeX Equation: {latex_string}</i>", body_style))
                
                # Add explanation - FIXED: Use ListFlowable instead of individual ListItems
                explanation_lines = explanation_text.split('\n')
                bullet_items = []
                regular_lines = []
                
                for line in explanation_lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('*'):
                        bullet_items.append(Paragraph(line.strip(' *'), bullet_style))
                    else:
                        regular_lines.append(line)
                
                # Add bullet points as a single ListFlowable
                if bullet_items:
                    bullet_list = ListFlowable(bullet_items, bulletType='bullet')
                    story.append(bullet_list)
                    story.append(Spacer(1, 6))
                
                # Add regular lines
                for line in regular_lines:
                    story.append(Paragraph(line, body_style))
                
                story.append(Spacer(1, 12))
                
            else:
                # Regular text section without equation
                for line in section.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('###'):
                        # Subheading
                        story.append(Paragraph(line.replace('###', '').strip(), styles['Heading3']))
                    elif line.startswith('*'):
                        # For single bullet points in regular text, just format as paragraph with bullet
                        story.append(Paragraph("• " + line.strip(' *'), body_style))
                    else:
                        # Regular paragraph
                        story.append(Paragraph(line, body_style))
                story.append(Spacer(1, 12))

    try:
        doc.build(story)
        print(f"✅ Successfully created PDF: {output_pdf_name}")
    except Exception as e:
        print(f"❌ Error building the PDF: {e}")

# --- Targeted Summarization ---
def get_section_from_gemini(pdf_path, extracted_text, section="summary"):
    """
    Extract a specific section (summary, methodology, equations, citations, future scope)
    and ask Gemini to explain it in detail with research insights and suggestions.
    """

    # --- Enhanced mentor-style prompts ---
    section_prompts = {
        "summary": """
        You are an expert academic assistant. Summarize the given research paper. 
        - First, extract and summarize the main objectives, methods, results, and contributions from the text. 
        - Keep it accurate and faithful to the paper. 
        - Then, provide an extended explanation of why this paper is important, how it fits in the broader research area, and how a student or researcher could learn from it or build upon it. 
        - Make the summary structured and easy to read.
        """,

        "methodology": """
        You are an expert academic assistant. Extract and explain the methodology section of the paper in detail. 
        - First, summarize the methodology as written in the paper: experimental setup, dataset, evaluation methods, and models used. 
        - Then, re-explain the methodology in simpler terms, as if teaching a student. 
        - Finally, suggest potential ways to extend or improve upon this methodology for future research projects.
        """,

        "equations": """
        You are an expert academic assistant. Extract and list all equations from the paper. 
        - First, reproduce the equations in LaTeX format and explain what each variable means. 
        - Then, explain each equation in plain English, showing how it fits into the research. 
        - Finally, suggest possible modifications or extensions of these equations that a researcher could test in future work.
        """,

        "citations": """
        You are an expert academic assistant. Extract all references from the paper. 
        - First, return the clean citation (authors, title, year, venue). 
        - Then, if possible, generate a direct link (DOI, arXiv, or Google Scholar link). 
        - Finally, explain why each reference is relevant to the paper and how it connects to the current research. 
        - If I am a student, suggest which of these references I should read first to understand the topic better.
        """,

        "future scope": """
        You are an academic assistant. Analyze the "Future Work" or "Conclusion" sections of the paper. 
        - First, summarize the future work explicitly mentioned by the authors. 
        - Then, expand with additional future research directions, open problems, and unexplored areas that logically follow from the paper. 
        - Suggest practical project ideas that a student or researcher could take up to extend this work. 
        - Think critically and creatively, as if you are advising a graduate student.
        """
    }

    # Pick the right prompt
    prompt = section_prompts.get(section.lower(), section_prompts["summary"])

    # --- Call Gemini ---
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content([
            f"Research Paper Extract:\n{extracted_text}\n\n",
            f"Task: {prompt}"
        ])
        return response.text
    except Exception as e:
        print(f"❌ Error while extracting section '{section}': {e}")
        return None


# --- Citations Extraction ---
def extract_citations_from_references(pdf_path):
    """
    Extract citations from the References section by detecting
    patterns like 'Author, A. Author. YEAR. Title...'.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return []

    # --- 1. Locate the References section ---
    match = re.search(r"(references|bibliography)(.*)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        print("⚠️ Could not find References section.")
        return []

    refs_text = match.group(2)

    # --- 2. Split citations ---
    # Each citation usually starts with: Capitalized name(s), then year (19xx or 20xx).
    raw_refs = re.split(r"(?=\n?[A-Z][a-zA-Z\-\']+.*\d{4}\.)", refs_text)

    references = []
    for ref in raw_refs:
        ref = ref.strip().replace("\n", " ")
        if len(ref) > 50 and re.search(r"\d{4}", ref):  # must contain a year
            references.append(ref)

    print(f"📚 Grouped into {len(references)} citations.")

    # --- 3. Enrich with DOI/links ---
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
