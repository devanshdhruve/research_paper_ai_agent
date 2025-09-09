from extractors.image_extractor import extract_images_and_captions

def get_multimodal_summary_from_gemini(pdf_path, text_content, gemini_client, similar_papers=None, text_only=False):
    if text_only:
        # Text-only processing mode
        memory_context = ""
        if similar_papers:
            memory_context = f"""
            RELATED RESEARCH CONTEXT:
            I found {len(similar_papers)} similar papers in our database:
            {', '.join([p['metadata'].get('title', 'Unknown title') for p in similar_papers])}
            
            Please consider this existing research when analyzing the new paper and highlight how this work differs or builds upon previous research.
            """
        
        prompt = f"""
        # COMPREHENSIVE RESEARCH PAPER ANALYSIS
        ## Role: Senior Research Analyst
        ## Task: Deep academic analysis of research paper
        
        {memory_context}
        
        ## ANALYSIS FRAMEWORK:
        You are conducting a thorough academic review of this research paper. Provide a structured, detailed analysis suitable for researchers, graduate students, and academic professionals.

        ## CRITICAL REQUIREMENTS:
        1. Be comprehensive but concise - avoid fluff, focus on substantive content
        2. Cross-reference information across different sections of the paper
        3. Identify both explicit and implicit contributions
        4. Provide critical analysis, not just summarization
        5. Use academic tone and precise terminology
        6. Include specific metrics, numbers, and quantitative results when available
        7. Highlight novel methodological approaches
        8. Connect findings to broader research landscape

        ## OUTPUT STRUCTURE (USE EXACT HEADINGS):

        ### 📋 Executive Overview
        - **Core Research Question**: What fundamental problem does this paper address?
        - **Primary Contribution**: What is the novel addition to the field?
        - **Significance**: Why does this matter in the broader research context?
        - **Target Audience**: Which research communities would benefit most from this work?

        ### 🎯 Research Gap & Motivation
        - **Identified Limitations**: What gaps in previous research does this paper address?
        - **Theoretical Motivation**: What theoretical frameworks or previous findings motivated this work?
        - **Practical Motivation**: What real-world problems or applications drive this research?
        - **Timeliness**: Why is this research particularly relevant now?

        ### 🔬 Methodology Deep Dive
        - **Experimental Design**: Detailed description of research design and approach
        - **Data Sources**: Datasets used, collection methods, and preprocessing steps
        - **Technical Approach**: Algorithms, models, or theoretical frameworks employed
        - **Evaluation Metrics**: Specific metrics used for validation and comparison
        - **Statistical Methods**: Analysis techniques and significance testing approaches
        - **Reproducibility**: Information available for replication of results

        ### 📊 Key Findings & Results
        - **Primary Results**: Main quantitative and qualitative findings
        - **Statistical Significance**: p-values, confidence intervals, effect sizes
        - **Comparative Performance**: How results compare to baseline or state-of-the-art
        - **Unexpected Findings**: Surprising or counterintuitive results
        - **Result Validation**: Methods used to verify and validate findings

        ### 🏛️ Theoretical Framework
        - **Theoretical Foundations**: Underlying theories and conceptual models
        - **Conceptual Contributions**: New theoretical constructs or frameworks
        - **Paradigm Alignment**: How this work fits within existing research paradigms
        - **Conceptual Innovation**: Novel ways of thinking about the problem

        ### 📚 Literature Context & Positioning
        - **Seminal References**: Key papers that form the foundation of this work
        - **Direct Comparisons**: How this work specifically differs from closest related papers
        - **Research Trajectory**: How this work moves the field forward
        - **Interdisciplinary Connections**: Links to other research domains

        ### ⚠️ Limitations & Constraints
        - **Acknowledged Limitations**: Limitations explicitly stated by authors
        - **Identified Constraints**: Additional constraints evident from methodology
        - **Generalizability**: Domain and application limitations
        - **Methodological Constraints**: Limitations in experimental design or approach
        - **Data Limitations**: Issues with dataset size, quality, or representativeness

        ### 🔮 Future Research Directions
        - **Author-Suggested Directions**: Future work explicitly recommended by authors
        - **Derived Opportunities**: Additional research avenues based on findings
        - **Technical Extensions**: Potential methodological improvements
        - **Application Expansions**: New domains or applications for this research
        - **Theoretical Developments**: Opportunities for theoretical advancement

        ### 🎓 Practical Implications
        - **Academic Impact**: How this influences future research and theory
        - **Practical Applications**: Real-world implementations and use cases
        - **Policy Implications**: Potential influence on guidelines or regulations
        - **Educational Value**: How this could be incorporated into curricula

        ### 💡 Critical Assessment
        - **Methodological Rigor**: Strength of experimental design and analysis
        - **Argumentation Quality**: Logical flow and evidence support
        - **Innovation Level**: Degree of novelty and creativity
        - **Impact Potential**: Likelihood of influencing the field
        - **Clarity and Presentation**: Quality of writing and organization

        ## RESEARCH PAPER TEXT:
        {text_content}
        """
        
        print("🧠 Sending comprehensive analysis request to Gemini (text-only mode)...")
        return gemini_client.generate_text(prompt)
    
    else:
        # Multimodal processing with images
        figures_text, selected_images = extract_images_and_captions(pdf_path, max_selected=5, manual=False)
        
        memory_context = ""
        if similar_papers:
            memory_context = f"""
            RELATED RESEARCH CONTEXT:
            I found {len(similar_papers)} similar papers in our database:
            {', '.join([p['metadata'].get('title', 'Unknown title') for p in similar_papers])}
            
            Please consider this existing research when analyzing the new paper and highlight how this work differs or builds upon previous research.
            """
        
        prompt = f"""
        # COMPREHENSIVE RESEARCH PAPER ANALYSIS
        ## Role: Senior Research Analyst
        ## Task: Deep academic analysis of research paper with multimodal data
        
        {memory_context}
        
        ## ANALYSIS FRAMEWORK:
        You are conducting a thorough academic review using both text content and visual elements. Provide a structured, detailed analysis suitable for researchers, graduate students, and academic professionals.

        ## MULTIMODAL INTEGRATION:
        - Cross-reference text descriptions with visual content
        - Verify that figures support textual claims
        - Extract quantitative data from charts and tables
        - Analyze diagrammatic representations of concepts
        - Assess visual presentation quality and clarity

        ## CRITICAL REQUIREMENTS:
        1. Integrate information from both text and visual elements
        2. Be comprehensive but concise - avoid fluff, focus on substantive content
        3. Provide critical analysis, not just summarization
        4. Use academic tone and precise terminology
        5. Include specific metrics, numbers, and quantitative results from both text and figures
        6. Highlight novel methodological approaches
        7. Connect findings to broader research landscape

        ## OUTPUT STRUCTURE (USE EXACT HEADINGS):

        ### 📋 Executive Overview
        - **Core Research Question**: What fundamental problem does this paper address?
        - **Primary Contribution**: What is the novel addition to the field?
        - **Significance**: Why does this matter in the broader research context?
        - **Target Audience**: Which research communities would benefit most from this work?

        ### 🎯 Research Gap & Motivation
        - **Identified Limitations**: What gaps in previous research does this paper address?
        - **Theoretical Motivation**: What theoretical frameworks or previous findings motivated this work?
        - **Practical Motivation**: What real-world problems or applications drive this research?

        ### 🔬 Methodology Deep Dive
        - **Experimental Design**: Detailed description of research design and approach
        - **Data Sources**: Datasets used, collection methods, and preprocessing steps
        - **Technical Approach**: Algorithms, models, or theoretical frameworks employed
        - **Evaluation Metrics**: Specific metrics used for validation and comparison
        - **Visual Methodology**: Analysis of methodological diagrams and flowcharts

        ### 📊 Key Findings & Results
        - **Primary Results**: Main quantitative and qualitative findings
        - **Visual Data Analysis**: Extraction and interpretation of data from figures, charts, and tables
        - **Statistical Significance**: p-values, confidence intervals, effect sizes from both text and figures
        - **Comparative Performance**: How results compare to baseline or state-of-the-art
        - **Result Validation**: Methods used to verify and validate findings

        ### 🏛️ Theoretical Framework
        - **Theoretical Foundations**: Underlying theories and conceptual models
        - **Conceptual Contributions**: New theoretical constructs or frameworks
        - **Visual Conceptualization**: Analysis of conceptual diagrams and models

        ### 📚 Literature Context & Positioning
        - **Seminal References**: Key papers that form the foundation of this work
        - **Direct Comparisons**: How this work specifically differs from closest related papers

        ### ⚠️ Limitations & Constraints
        - **Acknowledged Limitations**: Limitations explicitly stated by authors
        - **Identified Constraints**: Additional constraints evident from methodology and visual data
        - **Generalizability**: Domain and application limitations

        ### 🔮 Future Research Directions
        - **Author-Suggested Directions**: Future work explicitly recommended by authors
        - **Derived Opportunities**: Additional research avenues based on findings and visual data

        ### 🎓 Practical Implications
        - **Academic Impact**: How this influences future research and theory
        - **Practical Applications**: Real-world implementations and use cases

        ### 💡 Critical Assessment
        - **Methodological Rigor**: Strength of experimental design and analysis
        - **Visual Communication**: Effectiveness of figures and diagrams
        - **Innovation Level**: Degree of novelty and creativity

        ## VISUAL CONTENT ANALYSIS:
        Below are extracted figures, captions, and OCR text from the paper. Integrate this visual information with the text analysis:

        {figures_text}

        ## RESEARCH PAPER TEXT:
        {text_content}
        """
        
        content = [prompt, text_content]
        content.extend(selected_images)
        
        print("🧠 Sending comprehensive multimodal analysis request to Gemini...")
        return gemini_client.generate_content(content)