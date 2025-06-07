import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from document_processor import DocumentProcessor
from llm_rag import ChatbotLLM

def test_pdf_processing():
    print("Testing PDF processing...")
    
    # Initialize document processor
    doc_processor = DocumentProcessor()
    
    # Path to the uploads directory
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # Check if uploads directory exists
    if not os.path.exists(uploads_dir):
        print(f"Error: '{uploads_dir}' directory does not exist.")
        os.makedirs(uploads_dir)
        print(f"Created '{uploads_dir}' directory. Please add some PDF files and try again.")
        return
    
    # Find PDF files in the uploads directory
    pdf_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in '{uploads_dir}'. Please add some PDF files and try again.")
        return
    
    print(f"Found {len(pdf_files)} PDF files in '{uploads_dir}':")
    for pdf_file in pdf_files:
        print(f"- {pdf_file}")
    
    # Process each PDF file
    for pdf_file in pdf_files:
        file_path = os.path.join(uploads_dir, pdf_file)
        print(f"\nProcessing PDF: {pdf_file}")
        
        try:
            # Extract text from PDF
            text = doc_processor._extract_text_from_pdf(file_path)
            print(f"Extracted {len(text)} characters from {pdf_file}")
            
            # Split text into chunks
            chunks = doc_processor.text_splitter.split_text(text)
            print(f"Split into {len(chunks)} chunks")
            
            # Create vector store
            if not doc_processor.vector_store:
                print("Creating new vector store...")
                doc_processor.vector_store = FAISS.from_texts(
                    chunks, 
                    embedding=doc_processor.embeddings
                )
            else:
                print("Adding to existing vector store...")
                doc_processor.vector_store.add_texts(chunks)
            
            print(f"Successfully processed {pdf_file}")
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
    
    # Test the chatbot with the processed PDFs
    if doc_processor.vector_store:
        print("\nInitializing chatbot with the processed documents...")
        chatbot = ChatbotLLM(doc_processor.vector_store)
        
        # Test questions
        test_questions = [
            "What is this document about?",
            "Can you summarize the key points?",
            "What are the main topics covered?"
        ]
        
        for question in test_questions:
            print(f"\nQuestion: {question}")
            try:
                result = chatbot.qa_chain.invoke({"query": question})
                print(f"Answer: {result.get('result', 'No answer found.')}")
            except Exception as e:
                print(f"Error getting answer: {str(e)}")
    else:
        print("No vector store was created. Check the PDF processing logs above for errors.")

if __name__ == "__main__":
    test_pdf_processing()
