import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# Extraction settings
MAX_IMAGES = 5
OCR_ENGINE = "pytesseract"

# PDF Generation settings
PAGE_SIZE = "A4"
MARGINS = {
    "right": 50,
    "left": 50,
    "top": 50,
    "bottom": 50
}