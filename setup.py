from setuptools import setup, find_packages

setup(
    name="pdf-chatbot",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyMuPDF",
        "pdfplumber",
        "langchain",
        "langchain-community",
        "sentence-transformers",
        "faiss-cpu",
        "Flask",
        "pypdf",
    ],
    entry_points={
        "console_scripts": [
            "pdf-chatbot-cli=src.cli:main",
            "pdf-chatbot-web=src.app:main",
        ],
    },
    python_requires=">=3.8",
    author="Manus AI",
    author_email="info@example.com",
    description="A local chatbot that reads PDFs and enables Q&A using embedded LLMs",
    keywords="pdf, chatbot, llm, rag",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

