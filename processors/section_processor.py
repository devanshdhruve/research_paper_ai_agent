def get_section_from_gemini(pdf_path, extracted_text, section, gemini_client):
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

        "future_scope": """
        You are an academic assistant. Analyze the "Future Work" or "Conclusion" sections of the paper. 
        - First, summarize the future work explicitly mentioned by the authors. 
        - Then, expand with additional future research directions, open problems, and unexplored areas that logically follow from the paper. 
        - Suggest practical project ideas that a student or researcher could take up to extend this work. 
        - Think critically and creatively, as if you are advising a graduate student.
        """
    }

    prompt = section_prompts.get(section.lower(), section_prompts["summary"])
    
    try:
        return gemini_client.generate_content([
            f"Research Paper Extract:\n{extracted_text}\n\n",
            f"Task: {prompt}"
        ])
    except Exception as e:
        print(f"❌ Error while extracting section '{section}': {e}")
        return None