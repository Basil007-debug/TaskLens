import pdfplumber
import re
import json
import os
import pytesseract
from datetime import datetime
from PIL import Image

# # Ensure Tesseract is installed
# !apt-get install -y tesseract-ocr
# !pip install pytesseract

class PDFExtractor:
    def __init__(self, pdf_path, output_image_dir):
        self.pdf_path = pdf_path
        self.output_image_dir = output_image_dir
        os.makedirs(self.output_image_dir, exist_ok=True)
        self.output = {
            "metadata": {},
            "code_blocks": [],
            "text_descriptions": [],
            "graphs": []
        }
    
    def is_code_line(self, line):
        code_patterns = [
            r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=.*$',
            r'^\s*(import|from)\s+[a-zA-Z_]+',
            r'^\s*def\s+[a-zA-Z_]+.*:$',
            r'^\s*#\s*.*$',
            r'^\s*[a-zA-Z_]+\(.*\)',
            r'^\s*if\s+.*:$',
            r'^\s*for\s+.*:$',
            r'^\s*while\s+.*:$',
            r'^\s*class\s+[a-zA-Z_]+.*:$',
            r'^\s*[0-9]+[smn]s/step',
            r'^\s*plt\..*',
        ]
        return any(re.match(pattern, line.strip()) for pattern in code_patterns)

    def extract_text_from_image(self, image_path):
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from {image_path}: {e}")
            return ""
    
    def extract_pdf_data(self):
        current_code_block = []
        current_text_block = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                if page_num == 1 and lines[0].strip():
                    try:
                        date_time_str = lines[0].split(',')[0].strip()
                        date_time = datetime.strptime(date_time_str, '%d/%m/%Y')
                        self.output["metadata"]["date"] = date_time.strftime('%Y-%m-%d')
                        self.output["metadata"]["time"] = lines[0].split(',')[1].strip()
                    except ValueError:
                        pass
                    if " - Colab" in lines[0]:
                        self.output["metadata"]["filename"] = lines[0].split(' - Colab')[0].split()[-1]
                
                for line in lines[1:]:
                    line = line.strip()
                    if not line or line.startswith('Page') or re.match(r'^\d+/\d+$', line):
                        continue
                    
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
                
                if current_code_block:
                    self.output["code_blocks"].append("\n".join(current_code_block))
                    current_code_block = []
                if current_text_block:
                    self.output["text_descriptions"].append("\n".join(current_text_block))
                    current_text_block = []
                
                for i, image in enumerate(page.images):
                    image_obj = pdf.pages[page_num - 1].to_image()
                    image_path = os.path.join(self.output_image_dir, f"page_{page_num}_graph_{i}.png")
                    image_obj.save(image_path, format="PNG")
                    extracted_text = self.extract_text_from_image(image_path)
                    self.output["graphs"].append({"image_path": image_path, "extracted_text": extracted_text})
        
        self.output["code_blocks"] = list(dict.fromkeys(self.output["code_blocks"]))
        self.output["text_descriptions"] = list(dict.fromkeys(self.output["text_descriptions"]))
        return self.output
    
    def save_to_json(self, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    pdf_path = "C:/Users/DELL/Downloads/task_evaluation_report.pdf"
    output_image_dir = "C:/Users/DELL/Downloads/extracted_images"
    
    extractor = PDFExtractor(pdf_path, output_image_dir)
    extracted_data = extractor.extract_pdf_data()
    
    print("Metadata:")
    print(json.dumps(extracted_data["metadata"], indent=2))
    
    print("\nCode Blocks:")
    for i, block in enumerate(extracted_data["code_blocks"], 1):
        print(f"\nBlock {i}:\n{block}")
    
    print("\nText Descriptions:")
    for i, desc in enumerate(extracted_data["text_descriptions"], 1):
        print(f"\nDescription {i}:\n{desc}")
    
    print("\nExtracted Graphs and OCR Results:")
    for graph in extracted_data["graphs"]:
        print(f"\nImage: {graph['image_path']}")
        print(f"OCR Text: {graph['extracted_text']}")
    
    extractor.save_to_json("extracted_data.json")
