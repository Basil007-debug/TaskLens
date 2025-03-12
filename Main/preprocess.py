import nltk
import json
import re
import string

# Download necessary NLTK resources
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")

class TextPreprocessor:
    def __init__(self, text):
        self.text = text
        self.stop_words = set(nltk.corpus.stopwords.words('english'))
        self.lemmatizer = nltk.stem.WordNetLemmatizer()

    def preprocess(self):
        text = self.text.lower().translate(str.maketrans("", "", string.punctuation))  # Remove punctuation
        tokens = nltk.word_tokenize(text)  # Tokenize words
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]  # Lemmatize & remove stopwords
        
        # Ensure readability by keeping important connecting words
        meaningful_words = {"not", "is", "are", "does", "do", "was", "were", "has", "have"}
        tokens = [token for token in tokens if token in meaningful_words or token not in self.stop_words]

        return " ".join(tokens)  # Reconstruct the sentence properly

class CodePreprocessor:
    def __init__(self, code):
        self.code = code

    def preprocess(self):
        code = re.sub(r"#.*", "", self.code)  # Remove comments
        code = re.sub(r"\s+", " ", code).strip()  # Remove extra whitespace
        
        # Ensure proper formatting
        return "\n".join([line.strip() for line in self.code.split(";")])  # Preserve line breaks

class DataPreprocessor:
    def __init__(self, input_file, output_file="cleaned_data.json"):
        self.input_file = input_file
        self.output_file = output_file
        self.data = self.load_data()

    def load_data(self):
        with open(self.input_file, "r") as f:
            data = json.load(f)
        # Ensure required keys exist
        data.setdefault("text_descriptions", [])
        data.setdefault("code_blocks", [])
        return data

    def process(self):
        self.data["text_descriptions"] = [TextPreprocessor(desc).preprocess() for desc in self.data["text_descriptions"]]
        self.data["code_blocks"] = [CodePreprocessor(block).preprocess() for block in self.data["code_blocks"]]

        with open(self.output_file, "w") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

        print(f"✅ Preprocessing complete! Data saved as '{self.output_file}'.")

# Run the preprocessing if executed as a script
if __name__ == "__main__":
    preprocessor = DataPreprocessor("extracted_data.json")
    preprocessor.process()