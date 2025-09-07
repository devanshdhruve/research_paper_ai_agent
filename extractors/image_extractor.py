import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

def extract_images_and_captions(pdf_path, max_selected=7, manual=False):
    print(f"🖼️  Starting image and caption extraction from: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    figures_info = []
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            page_text = page.get_text("text")
            captions = re.findall(r"(Figure\s?\d+[:.].*)", page_text, re.IGNORECASE)
            
            for img_index, img in enumerate(image_list, start=1):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                
                ocr_text = pytesseract.image_to_string(image)
                
                caption = captions[img_index-1] if img_index-1 < len(captions) else "No caption found"
                
                figures_info.append({
                    "page": page_num + 1,
                    "caption": caption.strip(),
                    "ocr": ocr_text.strip(),
                    "image": image
                })
        
        # Selection logic
        selected = [fig for fig in figures_info if fig["caption"].lower().startswith(("figure", "table"))]
        
        if not selected:
            keywords = ["accuracy", "result", "performance", "evaluation", "bias", 
                       "comparison", "ablation", "error", "score"]
            selected = [fig for fig in figures_info if any(k in fig["caption"].lower() for k in keywords)]
        
        if not selected:
            selected = figures_info[:max_selected]
        else:
            selected = selected[:max_selected]
        
        if manual: 
            print("\nAvailable figures:")
            for i, fig in enumerate(figures_info):
                print(f"{i+1}. Page {fig['page']} - Caption: {fig['caption']}...")
            chosen = input(f"Enter figure numbers to keep (comma-seperated, max {max_selected}): ")
            chosen_ids = [int(x.strip())-1 for x in chosen.split(",") if x.strip().isdigit()]
            selected = [figures_info[i] for i in chosen_ids if 0 <= i < len(figures_info)]
        
        figures_text = "\n\n".join(
            [f"[Figure on page {f['page']}] {f['caption']}\nOCR: {f['ocr']}" for f in figures_info]
        )
        
        if figures_info:
            print(f"✅ Success! Found {len(figures_info)} total figures. Selected {len(selected)} for analysis.")
        else:
            print("⚠️  No images found in the PDF.")
            
        return figures_text, [f["image"] for f in selected]
        
    except Exception as e:
        print(f"❌ An error occurred during image extraction: {e}")
        return "", []