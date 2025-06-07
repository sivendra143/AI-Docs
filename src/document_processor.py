# document_processor.py

import os
from pypdf import PdfReader  # Using pypdf instead of PyMuPDF
import docx
import csv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

class DocumentProcessor:
    def __init__(self, docs_folder="./docs/", config_path="config.json"):
        self.docs_folder = docs_folder
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        
    def _extract_text_from_pdf(self, file_path):
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text from PDF {file_path}: {e}")
        return text
    
    def _extract_text_from_docx(self, file_path):
        text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error extracting text from DOCX {file_path}: {e}")
        return text
    
    def _extract_text_from_txt(self, file_path):
        text = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            print(f"Error extracting text from TXT {file_path}: {e}")
        return text
    
    def _extract_text_from_csv(self, file_path):
        text = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    text += " | ".join(row) + "\n"
        except Exception as e:
            print(f"Error extracting text from CSV {file_path}: {e}")
        return text
    
    def process_documents(self):
        all_chunks = []
        if not os.path.exists(self.docs_folder):
            print(f"Documents folder '{self.docs_folder}' does not exist.")
            return
        
        for filename in os.listdir(self.docs_folder):
            file_path = os.path.join(self.docs_folder, filename)
            
            if not os.path.isfile(file_path):
                continue
                
            print(f"Processing {file_path}...")
            text = ""
            
            if filename.lower().endswith('.pdf'):
                text = self._extract_text_from_pdf(file_path)
            elif filename.lower().endswith('.docx'):
                text = self._extract_text_from_docx(file_path)
            elif filename.lower().endswith('.txt'):
                text = self._extract_text_from_txt(file_path)
            elif filename.lower().endswith('.csv'):
                text = self._extract_text_from_csv(file_path)
            else:
                print(f"Unsupported file format: {filename}")
                continue
            
            if text:
                chunks = self.text_splitter.split_text(text)
                all_chunks.extend(chunks)
        
        if all_chunks:
            self.vector_store = FAISS.from_texts(all_chunks, self.embeddings)
            print("Documents processed and embeddings generated. FAISS index created.")
        else:
            print("No document content to process.")
    
    def get_vector_store(self):
        return self.vector_store

if __name__ == "__main__":
    # Create a dummy docs folder and a dummy file for testing
    os.makedirs("docs", exist_ok=True)
    with open("docs/dummy.txt", "w") as f:
        f.write("This is a dummy text file content for testing purposes.")

    processor = DocumentProcessor()
    processor.process_documents()
    vector_store = processor.get_vector_store()
    if vector_store:
        print("Vector store is ready.")
    else:
        print("Vector store is empty.")

