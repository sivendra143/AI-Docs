import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

# Path to PDF directory
PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docs'))

# Load and split all PDFs in the directory
def load_and_split_pdfs(pdf_dir=PDF_DIR):
    docs = []
    for fname in os.listdir(pdf_dir):
        if fname.lower().endswith('.pdf'):
            loader = PyPDFLoader(os.path.join(pdf_dir, fname))
            docs.extend(loader.load())
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(docs)

# Build FAISS vector store from documents
def build_faiss_index(docs):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(docs, embeddings)

# Initialize on module load
doc_chunks = load_and_split_pdfs()
vector_store = build_faiss_index(doc_chunks) if doc_chunks else None

# Retrieve top-k relevant chunks for a query
def retrieve_context(question, k=4):
    if not vector_store:
        return []
    results = vector_store.similarity_search(question, k=k)
    return [r.page_content for r in results]
