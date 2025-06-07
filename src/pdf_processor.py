# pdf_processor.py

import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

class PDFProcessor:
    def __init__(self, pdf_folder="./pdf_docs/"):
        self.pdf_folder = pdf_folder
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None

    def _extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            document = fitz.open(pdf_path)
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text += page.get_text()
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
        return text

    def process_pdfs(self):
        all_chunks = []
        if not os.path.exists(self.pdf_folder):
            print(f"PDF folder '{self.pdf_folder}' does not exist.")
            return

        for filename in os.listdir(self.pdf_folder):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(self.pdf_folder, filename)
                print(f"Processing {pdf_path}...")
                text = self._extract_text_from_pdf(pdf_path)
                chunks = self.text_splitter.split_text(text)
                all_chunks.extend(chunks)
        
        if all_chunks:
            self.vector_store = FAISS.from_texts(all_chunks, self.embeddings)
            print("PDFs processed and embeddings generated. FAISS index created.")
        else:
            print("No PDF content to process.")

    def get_vector_store(self):
        return self.vector_store

if __name__ == "__main__":
    # Create a dummy pdf_docs folder and a dummy PDF file for testing
    os.makedirs("pdf_docs", exist_ok=True)
    with open("pdf_docs/dummy.pdf", "w") as f:
        f.write("This is a dummy PDF file content for testing purposes.")

    processor = PDFProcessor()
    processor.process_pdfs()
    vector_store = processor.get_vector_store()
    if vector_store:
        print("Vector store is ready.")
    else:
        print("Vector store is empty.")


