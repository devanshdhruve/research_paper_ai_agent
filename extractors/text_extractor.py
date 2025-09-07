from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    print(f"Reading text from: {pdf_path}")
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