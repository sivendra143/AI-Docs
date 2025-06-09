# AI Document Chat with RAG

A powerful document question-answering system that leverages Retrieval-Augmented Generation (RAG) to provide accurate, context-aware responses from your documents. Built with Python, Flask, LangChain, and modern web technologies.

![AI Document Chat Demo](https://via.placeholder.com/800x400.png?text=AI+Document+Chat+Demo)

## ✨ Features

- **Multi-Document Support**: Process and query across PDF, DOCX, TXT, CSV, and XLSX files
- **Advanced RAG Pipeline**: Combines retrieval and generation for accurate, context-aware responses
- **Real-time Interaction**: WebSocket-based chat interface with typing indicators
- **Conversation History**: Maintains context across multiple interactions
- **Local LLM Support**: Works with LM Studio, Ollama, or any OpenAI-compatible API
- **Vector Search**: FAISS-based semantic search for efficient document retrieval
- **Modern Web UI**: Responsive design with dark/light theme support
- **RESTful API**: Easy integration with other applications
- **Extensible Architecture**: Modular design for easy customization

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip (Python package manager)
- LM Studio or Ollama running locally (or access to an OpenAI-compatible API)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ai-docs.git
   cd ai-docs
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application**:
   - Copy `config.example.json` to `config.json`
   - Update the configuration with your LM Studio/Ollama settings

5. **Add documents**:
   - Place your documents in the `docs` folder
   - Supported formats: PDF, DOCX, TXT, CSV, XLSX

### Running the Application

1. **Start the backend server**:
   ```bash
   python run_app.py --debug
   ```

2. **Access the web interface**:
   - Open your browser and navigate to `http://localhost:5000`

## 🔧 Configuration

Edit `config.json` to customize the application behavior:

```json
{
  "document_processor": {
    "docs_folder": "docs",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "supported_file_types": ["pdf", "docx", "txt", "csv", "xlsx"]
  },
  "llm": {
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "embedding": {
    "model_name": "all-MiniLM-L6-v2"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": true
  }
}
```

## 🤖 Using Different LLM Backends

### LM Studio
1. Download and run [LM Studio](https://lmstudio.ai/)
2. Load your preferred model
3. Update `config.json` with the LM Studio API URL (default: `http://localhost:1234/v1`)

### Ollama
1. Install [Ollama](https://ollama.ai/)
2. Pull a model: `ollama pull llama3`
3. Update `config.json` with the Ollama API URL (default: `http://localhost:11434/v1`)

### OpenAI
1. Get your API key from [OpenAI](https://platform.openai.com/)
2. Set the `OPENAI_API_KEY` environment variable
3. Update `config.json` with the OpenAI model name (e.g., `gpt-4-turbo`)

## 📚 Documentation

### Project Structure

```
ai-docs/
├── docs/                    # Directory for document storage
├── src/                     # Source code
│   ├── __init__.py
│   ├── app.py               # Main application setup
│   ├── config.json          # Configuration file
│   ├── document_processor.py # Document processing logic
│   ├── llm_rag.py           # RAG implementation
│   ├── conversation_manager.py # Conversation management
│   ├── websocket.py         # WebSocket handlers
│   └── static/              # Frontend assets
│   └── templates/           # HTML templates
├── requirements.txt         # Python dependencies
└── run_app.py              # Application entry point
```

### API Endpoints

- `GET /`: Web interface
- `GET /api/health`: Health check
- `POST /api/chat`: Chat endpoint
- `POST /api/upload`: Document upload
- `GET /api/conversations`: List conversations
- `GET /api/conversations/<id>`: Get conversation history

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://python.langchain.com/) for the RAG framework
- [FAISS](https://github.com/facebookresearch/faiss) for efficient similarity search
- [LM Studio](https://lmstudio.ai/) and [Ollama](https://ollama.ai/) for local LLM support
- [Flask](https://flask.palletsprojects.com/) and [Flask-SocketIO](https://flask-socketio.readthedocs.io/) for the web framework

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
