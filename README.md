# PDF Chatbot

A local AI chatbot that reads PDFs and other document formats from a folder and enables Q&A using embedded LLMs (like Llama3 via LM Studio or Ollama).

## Features

- Scan a folder for PDF files and other document formats (DOCX, TXT, CSV, XLSX)
- Extract and chunk content using PyMuPDF or pdfplumber
- Generate embeddings using SentenceTransformers
- Index embeddings in FAISS for fast vector search
- Ask questions via Web UI
- Use a local LLM for RAG-style answers
- Fallback for out-of-scope queries
- Smart suggestions based on previous questions and context
- WebSocket for real-time communication
- Voice input using Whisper
- User Authentication with JWT
- Admin dashboard
- Dark/light theme toggle

## Requirements

- Python 3.8+
- Node.js 16+ (for frontend assets)
- Git

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-docs.git
cd ai-docs
```

### 2. Set Up the Environment

#### Windows

1. Run the setup script:
   ```powershell
   .\setup_env.ps1
   ```

2. Start the development server:
   ```powershell
   .\run.ps1
   ```

#### Linux/macOS

1. Make the setup script executable:
   ```bash
   chmod +x setup_env.sh
   ```

2. Run the setup script:
   ```bash
   ./setup_env.sh
   ```

3. Start the development server:
   ```bash
   ./run.sh
   ```

### 3. Access the Application

Open your web browser and navigate to:

```
http://localhost:5000
```

Default login credentials:
- Username: `admin`
- Password: `admin123`

## Configuration

Copy `.env.example` to `.env` and modify the settings as needed:

```bash
cp .env.example .env
```

Edit the `.env` file to customize your setup:

```env
# Application Settings
FLASK_APP=src.app:app
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=sqlite:///instance/chatbot.db

# File Uploads
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# CORS
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000,file://*

# Model Settings
MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Project Structure

```
.
├── src/                    # Application source code
│   ├── __init__.py         # Application factory
│   ├── app.py              # Main application module
│   ├── config.py           # Configuration settings
│   ├── models.py           # Database models
│   ├── routes.py           # API routes
│   ├── document_processor.py # Document processing logic
│   ├── llm_rag.py          # LLM and RAG implementation
│   ├── websocket.py        # WebSocket handlers
│   └── static/             # Static files (CSS, JS, images)
│   └── templates/          # HTML templates
├── tests/                  # Test files
├── uploads/                # User-uploaded files
├── .env.example            # Example environment variables
├── requirements.txt        # Python dependencies
├── setup_env.ps1           # Windows setup script
├── run.ps1                 # Windows run script
└── README.md               # This file
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

This project uses `black` for code formatting and `flake8` for linting.

```bash
# Format code
black .


# Lint code
flake8
```

## License

MIT
