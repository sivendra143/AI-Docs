# llm_rag.py

import json
import os
from openai import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class ChatbotLLM:
    def __init__(self, vector_store, config_path="config.json"):
        self.vector_store = vector_store
        self.config = self._load_config(config_path)
        self.llm = self._initialize_llm()
        self.qa_chain = self._initialize_qa_chain()

    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            return json.load(f)

    def _initialize_llm(self):
        # Set the OpenAI API base URL to point to LM Studio
        os.environ["OPENAI_API_BASE"] = self.config["llm_api_base"]
        # Use any non-empty string as the API key (LM Studio doesn't require a real key)
        os.environ["OPENAI_API_KEY"] = "lm-studio"
        
        # Create an OpenAI client
        client = OpenAI(
            base_url=self.config["llm_api_base"],
            api_key="lm-studio"
        )
        
        # Return a ChatOpenAI instance configured for LM Studio
        return ChatOpenAI(
            model=self.config["llm_model_path"],
            temperature=0.7,
            max_tokens=1000
        )

    def _initialize_qa_chain(self):
        if not self.vector_store:
            raise ValueError("Vector store is not initialized. Please process PDFs first.")

        # Custom prompt for RAG
        template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Keep the answer as concise as possible.

{context}

Question: {question}
Helpful Answer:"""
        QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )
        return qa_chain

    def ask_question(self, question):
        if not self.qa_chain:
            return "Error: Chatbot not initialized. Please process PDFs first."

        result = self.qa_chain({"query": question})
        answer = result["result"]
        source_documents = result["source_documents"]

        # Fallback for out-of-scope queries
        if "don't know" in answer.lower() or "not covered" in answer.lower():
            return "Sorry, this question is not covered in the uploaded documents. Please ask something else."

        return answer

    def get_smart_suggestions(self, previous_question, context):
        # This is a placeholder for smart suggestions. 
        # A more advanced implementation would involve analyzing the previous question, 
        # the context, and potentially the user's interaction history to generate relevant follow-up questions.
        return ["Can you elaborate on X?", "What about Y?", "Tell me more about Z."]

if __name__ == "__main__":
    # This is a placeholder for testing. In a real scenario, you would pass a populated vector_store.
    # For demonstration, we'll create a dummy vector_store.
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    from langchain_community.vectorstores import FAISS

    # Create a dummy vector store
    texts = ["The quick brown fox jumps over the lazy dog.", "Artificial intelligence is a rapidly developing field."]
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    dummy_vector_store = FAISS.from_texts(texts, embeddings)

    # Initialize ChatbotLLM with the dummy vector store
    chatbot = ChatbotLLM(dummy_vector_store)

    # Example usage
    question = "What is AI?"
    answer = chatbot.ask_question(question)
    print(f"Question: {question}")
    print(f"Answer: {answer}")

    question = "What is the capital of France?"
    answer = chatbot.ask_question(question)
    print(f"Question: {question}")
    print(f"Answer: {answer}")

    suggestions = chatbot.get_smart_suggestions("What is AI?", "Some context about AI.")
    print(f"Suggestions: {suggestions}")


