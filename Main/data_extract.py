# data_extract.py
import pdfplumber
import re
from io import BytesIO

class PDFExtractor:
    def __init__(self, pdf_file):
        """Initialize with a file-like object (e.g., BytesIO) instead of a file path."""
        self.pdf_file = pdf_file
        self.output = {
            "code_blocks": [],
            "text_descriptions": [],
            "plots":[]
        }

    def is_code_line(self, line):
        """Checks if a given line is a code snippet based on common patterns."""
        code_patterns = [
            r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=.*$',  # Variable assignment
            r'^\s*(import|from)\s+[a-zA-Z_]+',  # Imports
            r'^\s*def\s+[a-zA-Z_]+.*:$',  # Function definition
            r'^\s*#\s*.*$',  # Comments
            r'^\s*[a-zA-Z_]+\(.*\)',  # Function calls
            r'^\s*if\s+.*:$',  # If statement
            r'^\s*for\s+.*:$',  # For loop
            r'^\s*while\s+.*:$',  # While loop
            r'^\s*class\s+[a-zA-Z_]+.*:$',  # Class definition
            r'^\s*plt\..*',  # Matplotlib commands
        ]
        return any(re.match(pattern, line.strip()) for pattern in code_patterns)

    def extract_pdf_data(self):
        """Extracts text and categorizes it into code blocks and text descriptions."""
        current_code_block = []
        current_text_block = []

        try:
            with pdfplumber.open(self.pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('Page') or re.match(r'^\d+/\d+$', line):
                            continue  # Skip page numbers or empty lines

                        if self.is_code_line(line):
                            if current_text_block:
                                self.output["text_descriptions"].append("\n".join(current_text_block))
                                current_text_block = []
                            current_code_block.append(line)
                        else:
                            if current_code_block:
                                self.output["code_blocks"].append("\n".join(current_code_block))
                                current_code_block = []
                            current_text_block.append(line)

                    # Capture remaining blocks at the end of the page
                    if current_code_block:
                        self.output["code_blocks"].append("\n".join(current_code_block))
                        current_code_block = []
                    if current_text_block:
                        self.output["text_descriptions"].append("\n".join(current_text_block))
                        current_text_block = []

            return self.output
        except Exception as e:
            raise ValueError(f"Error extracting data from PDF: {str(e)}")