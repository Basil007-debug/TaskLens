# preprocess.py
import re

class TextPreprocessor:
    def clean_text(self, text):
        """Cleans extracted text by removing unwanted characters and formatting issues."""
        if not isinstance(text, str):
            return ""
        # Remove repeated nonsense (e.g., 'printf' spam)
        text = re.sub(r'(\b\w+\b)(?:\s+\1)+', r'\1', text)
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize spaces
        text = re.sub(r'[^\w\s.,!?]', '', text)  # Remove unwanted special characters
        return text

    def clean_code(self, code):
        """Cleans code blocks by preserving structure while removing excess whitespace."""
        if not isinstance(code, str):
            return ""
        code = re.sub(r'\n\s*\n', '\n', code.strip())
        return code

    def preprocess(self, extracted_data):
        """Preprocess extracted text and return cleaned data."""
        if not isinstance(extracted_data, dict):
            raise TypeError(f"Expected a dictionary but got {type(extracted_data)}")

        processed_data = {
            "text_descriptions": [],
            "code_blocks": []
        }

        for text in extracted_data.get("text_descriptions", []):
            cleaned_text = self.clean_text(text)
            if cleaned_text:
                processed_data["text_descriptions"].append(cleaned_text)

        for code in extracted_data.get("code_blocks", []):
            cleaned_code = self.clean_code(code)
            if cleaned_code:
                processed_data["code_blocks"].append(cleaned_code)

        return processed_data