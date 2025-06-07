# PDF Chatbot

A local AI chatbot that reads PDFs and other document formats from a folder and enables Q&A using embedded LLMs (like Llama3 via LM Studio or Ollama).

## Features

- Scan a folder for PDF files and other document formats (DOCX, TXT, CSV)
- Extract and chunk content using PyMuPDF or pdfplumber
- Generate embeddings using SentenceTransformers
- Index embeddings in FAISS for fast vector search
- Ask questions via CLI or Web UI
- Use a local LLM via LM Studio or Ollama for RAG-style answers
- Fallback for out-of-scope queries
- Smart suggestions based on previous questions and context
- WebSocket for real-time communication
- Voice input using Whisper
- User Authentication with JWT
- Admin analytics dashboard
- Dark/light theme toggle
- Packaged build with Docker support

## Requirements

- Python 3.8+
- LM Studio or Ollama for local LLM access

## Installation

### Option 1: Using pip

```bash
pip install -r requirements.txt
```

### Option 2: Using Docker

```bash
docker build -t pdf-chatbot .
```

Or using docker-compose:

```bash
docker-compose up -d
```

## Configuration

Edit the `config.json` file to customize your setup:

```json
{
    "docs_folder": "./docs/",
    "supported_file_types": ["pdf", "docx", "txt", "csv"],
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_model_path": "",
    "llm_api_base": "http://localhost:11434/v1",
    "ui_type": "web",
    "host": "0.0.0.0",
    "port": 5000
}
```

## Usage

### CLI Interface

```bash
./run_cli.sh
```

Or:

```bash
python src/cli.py
```

### Web Interface

```bash
./run_web.sh
```

Or:

```bash
python src/app.py
```

Then open your browser to http://localhost:5000

## Admin Dashboard

Access the admin dashboard at http://localhost:5000/admin

Default credentials:
- Username: admin
- Password: admin123

## Project Structure

```
chatbot_project/
├── config.json           # Configuration file
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
├── run_cli.sh            # CLI executable script
├── run_web.sh            # Web executable script
├── setup.py              # Package setup file
├── MANIFEST.in           # Package manifest
├── docs/                 # Default folder for documents
└── src/                  # Source code
    ├── app.py            # Web application
    ├── cli.py            # CLI application
    ├── document_processor.py # Multi-format document processor
    ├── llm_rag.py        # LLM and RAG implementation
    ├── voice_input.py    # Voice input processing
    ├── api.py            # API endpoints
    ├── websocket.py      # WebSocket implementation
    ├── templates/        # HTML templates
    │   ├── index.html    # Main web interface
    │   ├── login.html    # Login page
    │   └── admin.html    # Admin dashboard
    └── static/           # Static assets
        ├── css/          # CSS styles
        │   ├── styles.css
        │   ├── login.css
        │   ├── voice.css
        │   └── admin/
        │       └── admin.css
        └── js/           # JavaScript files
            ├── script.js
            ├── theme.js
            ├── analytics.js
            └── voice/
                └── voice.js
```

## License

MIT

## Author

Manus AI

