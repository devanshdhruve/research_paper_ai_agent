import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def generate_content(self, content):
        """Wrapper for Gemini's generate_content with error handling"""
        try:
            response = self.model.generate_content(content)
            return response.text
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return None