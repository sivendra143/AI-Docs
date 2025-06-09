# document_processor.py

import os
from pypdf import PdfReader  # Using pypdf instead of PyMuPDF
import docx
import csv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

class DocumentProcessor:
    def __init__(self, docs_folder=None, config=None, config_path="config.json"):
        # Store configuration
        self.config = self._load_config(config_path) if config is None else config
        
        # Set up document processing parameters
        self.docs_folder = docs_folder or self.config.get('docs_folder', './docs/')
        
        # Ensure the docs folder exists
        os.makedirs(self.docs_folder, exist_ok=True)
        
        # Initialize text splitter with config values
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.get('chunk_size', 1000),
            chunk_overlap=self.config.get('chunk_overlap', 200),
            length_function=len,
        )
        
        # Initialize embeddings
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=self.config.get('embedding_model', 'all-MiniLM-L6-v2')
        )
        self.vector_store = None
    
    def _load_config(self, config_path):
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            print(f"⚠️ Config file not found at {config_path}, using defaults")
            return {}
            
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading config from {config_path}: {e}")
            return {}
        
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
        """Process all documents in the docs folder and create a vector store."""
        all_chunks = []
        
        # Ensure the docs folder exists
        if not os.path.exists(self.docs_folder):
            print(f"⚠️ Documents folder '{self.docs_folder}' does not exist.")
            os.makedirs(self.docs_folder, exist_ok=True)
            print(f"📁 Created empty docs folder at: {self.docs_folder}")
            return False
        
        # Get list of supported file types from config or use default
        supported_types = self.config.get('supported_file_types', ['pdf', 'docx', 'txt', 'csv'])
        print(f"📂 Processing documents in: {self.docs_folder}")
        print(f"📄 Supported file types: {', '.join(supported_types)}")
        
        # Process each file in the docs folder
        processed_files = 0
        for filename in os.listdir(self.docs_folder):
            file_path = os.path.join(self.docs_folder, filename)
            
            # Skip directories and non-supported files
            if not os.path.isfile(file_path):
                continue
                
            # Check file extension
            file_ext = filename.split('.')[-1].lower()
            if file_ext not in supported_types:
                print(f"  ⏩ Skipping unsupported file: {filename}")
                continue
                
            print(f"  📄 Processing: {filename}")
            try:
                text = ""
                
                # Extract text based on file type
                if filename.lower().endswith('.pdf'):
                    text = self._extract_text_from_pdf(file_path)
                elif filename.lower().endswith('.docx'):
                    text = self._extract_text_from_docx(file_path)
                elif filename.lower().endswith('.txt'):
                    text = self._extract_text_from_txt(file_path)
                elif filename.lower().endswith('.csv'):
                    text = self._extract_text_from_csv(file_path)
                
                # Process the extracted text
                if text and text.strip():
                    # Clean and normalize the text
                    text = ' '.join(text.split())
                    
                    # Split into chunks
                    chunks = self.text_splitter.split_text(text)
                    
                    # Add metadata to each chunk
                    for chunk in chunks:
                        all_chunks.append({
                            'text': chunk,
                            'metadata': {
                                'source': filename,
                                'chunk_id': f"{filename}_{len(all_chunks)}"
                            }
                        })
                    
                    print(f"    ✅ Extracted {len(chunks)} chunks from {filename}")
                    processed_files += 1
                else:
                    print(f"    ⚠️ No text extracted from {filename}")
                    
            except Exception as e:
                print(f"    ❌ Error processing {filename}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Create vector store if we have chunks
        if all_chunks:
            try:
                print(f"\n🔧 Creating vector store with {len(all_chunks)} chunks...")
                
                # Extract texts and metadatas
                texts = [chunk['text'] for chunk in all_chunks]
                metadatas = [chunk['metadata'] for chunk in all_chunks]
                
                # Create the vector store
                self.vector_store = FAISS.from_texts(
                    texts=texts,
                    embedding=self.embeddings,
                    metadatas=metadatas
                )
                
                print("✅ Vector store created successfully!")
                print(f"   - Total documents: {processed_files}")
                print(f"   - Total chunks: {len(all_chunks)}")
                print(f"   - Embedding model: {self.embeddings.model_name}")
                
                return True
                
            except Exception as e:
                print(f"❌ Failed to create vector store: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("ℹ️ No valid text chunks were extracted from the documents.")
            return False
    
    def get_vector_store(self):
        """Get the vector store, initializing it if necessary."""
        if self.vector_store is None:
            print("ℹ️ Vector store not initialized. Processing documents...")
            if not self.process_documents():
                print("❌ Failed to initialize vector store")
                return None
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

