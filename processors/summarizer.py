from extractors.image_extractor import extract_images_and_captions

def get_multimodal_summary_from_gemini(pdf_path, text_content, gemini_client):
    figures_text, selected_images = extract_images_and_captions(pdf_path, max_selected=5, manual=False)
    
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
    
    content = [prompt, text_content]
    content.extend(selected_images)
    
    print("🧠 Sending text + figures to Gemini for summarization...")
    return gemini_client.generate_content(content)