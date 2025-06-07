# User Guide

This guide provides detailed instructions for setting up and using the PDF Chatbot.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Using the CLI Interface](#using-the-cli-interface)
4. [Using the Web Interface](#using-the-web-interface)
5. [Adding Documents](#adding-documents)
6. [Asking Questions](#asking-questions)
7. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- LM Studio or Ollama for local LLM access
- Docker (optional, for containerized deployment)

### Option 1: Local Installation

1. Clone the repository or extract the provided archive:

```bash
git clone https://github.com/yourusername/pdf-chatbot.git
cd pdf-chatbot
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a folder for your PDF documents:

```bash
mkdir -p pdf_docs
```

### Option 2: Docker Installation

1. Build the Docker image:

```bash
docker build -t pdf-chatbot .
```

2. Run the container:

```bash
docker run -p 5000:5000 -v $(pwd)/pdf_docs:/app/pdf_docs pdf-chatbot
```

Alternatively, use Docker Compose:

```bash
docker-compose up -d
```

## Configuration

The chatbot is configured using the `config.json` file. Here's what each setting means:

| Setting | Description | Default |
|---------|-------------|---------|
| `pdf_folder` | Path to the folder containing PDF documents | `./pdf_docs/` |
| `chunk_size` | Size of text chunks for processing | `1000` |
| `chunk_overlap` | Overlap between chunks to maintain context | `200` |
| `embedding_model` | Model used for generating embeddings | `all-MiniLM-L6-v2` |
| `llm_model_path` | Path to local LLM model (if using LM Studio) | `""` |
| `llm_api_base` | API endpoint for LLM (if using Ollama) | `http://localhost:11434/v1` |
| `ui_type` | Type of user interface to use (`cli` or `web`) | `web` |
| `host` | Host address for web interface | `0.0.0.0` |
| `port` | Port for web interface | `5000` |

### Setting Up Ollama

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull a model (e.g., Llama3):

```bash
ollama pull llama3
```

3. Start the Ollama server:

```bash
ollama serve
```

4. Update the `config.json` file to use Ollama:

```json
{
    "llm_model_path": "llama3",
    "llm_api_base": "http://localhost:11434/v1"
}
```

### Setting Up LM Studio

1. Download and install LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. Download a model through the LM Studio interface
3. Start the local server in LM Studio
4. Update the `config.json` file to use LM Studio:

```json
{
    "llm_api_base": "http://localhost:1234/v1"
}
```

## Using the CLI Interface

1. Start the CLI interface:

```bash
./run_cli.sh
```

Or:

```bash
python src/cli.py
```

2. The chatbot will process any PDF files in the configured folder
3. Once processing is complete, you can start asking questions
4. Type your questions and press Enter
5. To exit, type `exit`, `quit`, or `q`

### CLI Options

You can customize the CLI behavior with command-line arguments:

```bash
python src/cli.py --config custom_config.json --pdf_folder /path/to/pdfs
```

| Option | Description |
|--------|-------------|
| `--config` | Path to a custom configuration file |
| `--pdf_folder` | Path to a custom PDF folder (overrides config) |

## Using the Web Interface

1. Start the web interface:

```bash
./run_web.sh
```

Or:

```bash
python src/app.py
```

2. Open your web browser and navigate to http://localhost:5000
3. The chatbot will process any PDF files in the configured folder
4. Once processing is complete, you can start asking questions using the input field

### Web Interface Features

- **Chat History**: All questions and answers are displayed in a chat-like interface
- **Suggestions**: The chatbot provides suggested follow-up questions
- **Theme Toggle**: Switch between light and dark themes using the toggle button
- **Refresh Button**: Reload PDF documents if you've added new ones

## Adding Documents

1. Place your PDF files in the configured folder (default: `./pdf_docs/`)
2. If the chatbot is already running:
   - In the CLI interface, restart the application
   - In the web interface, click the "Refresh PDFs" button

### Supported Document Types

The base version supports PDF files. With upgrades, the following formats are also supported:

- DOCX (Microsoft Word)
- TXT (Plain text)
- CSV (Comma-separated values)

## Asking Questions

The chatbot is designed to answer questions based on the content of your documents. Here are some tips for effective questioning:

- **Be specific**: Ask clear, focused questions
- **Use context**: Reference specific documents or topics when possible
- **Follow up**: Use the suggested follow-up questions or ask for clarification
- **Try variations**: If you don't get a satisfactory answer, try rephrasing the question

### Example Questions

- "What are the key points in the quarterly report?"
- "Summarize the methodology section of the research paper."
- "What did the author say about climate change in chapter 3?"
- "Compare the financial results from 2023 and 2024."

## Troubleshooting

### Common Issues

#### No PDF Content Processed

**Problem**: The chatbot reports "No PDF content to process."

**Solutions**:
- Check that PDF files exist in the configured folder
- Ensure the PDF files are readable and not password-protected
- Try a different PDF file to rule out corruption issues

#### LLM Connection Failed

**Problem**: The chatbot cannot connect to the LLM.

**Solutions**:
- Ensure Ollama or LM Studio is running
- Check the API base URL in the configuration
- Verify that the specified model is available

#### Web Interface Not Loading

**Problem**: The web interface doesn't load or shows errors.

**Solutions**:
- Check that the server is running (look for "Running on http://0.0.0.0:5000")
- Ensure no other application is using port 5000
- Try accessing with http://localhost:5000 instead of 0.0.0.0

#### Docker Issues

**Problem**: Docker container fails to start or access files.

**Solutions**:
- Ensure Docker is installed and running
- Check that the volume mounting is correct
- Verify permissions on the pdf_docs folder

### Getting Help

If you encounter issues not covered in this guide:

1. Check the console output for error messages
2. Review the configuration settings
3. Restart the application
4. Check for updates to the chatbot

## Conclusion

The PDF Chatbot provides a powerful way to interact with your documents using natural language. By following this guide, you should be able to set up and use the chatbot effectively. As you become more familiar with the system, you can explore the advanced features and customization options available.

