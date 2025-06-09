.. _getting-started:

Getting Started
==============

This guide will help you get started with AI Document Chat.

Installation
------------

Prerequisites
~~~~~~~~~~~~~

- Python 3.10 or higher
- pip (Python package manager)
- Git (optional, for development)

Installation Steps
~~~~~~~~~~~~~~~~~~

1. Clone the repository (if you haven't already):

   .. code-block:: bash

      git clone https://github.com/yourusername/ai-document-chat.git
      cd ai-document-chat

2. Create a virtual environment (recommended):

   .. code-block:: bash

      # On Windows
      python -m venv venv
      .\\venv\\Scripts\\activate

      # On macOS/Linux
      python3 -m venv venv
      source venv/bin/activate

3. Install the required dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

4. Install the package in development mode (optional):

   .. code-block:: bash

      pip install -e .

Configuration
-------------

1. Copy the example configuration file:

   .. code-block:: bash

      cp config.example.json config.json

2. Edit the ``config.json`` file to configure your settings:

   - Set your OpenAI API key
   - Configure the document processing settings
   - Adjust the model parameters as needed

   Example configuration:

   .. code-block:: json

      {
        "document_processor": {
          "docs_folder": "docs",
          "chunk_size": 1000,
          "chunk_overlap": 200
        },
        "llm": {
          "model_name": "gpt-3.5-turbo",
          "temperature": 0.7,
          "max_tokens": 1000
        },
        "server": {
          "host": "0.0.0.0",
          "port": 5000,
          "debug": true
        }
      }

Running the Application
----------------------

Start the development server:

.. code-block:: bash

   python run_app.py

Or for development with auto-reload:

.. code-block:: bash

   python run_dev.py

The application will be available at http://localhost:5000

Docker Support
-------------

You can also run the application using Docker:

1. Build the Docker image:

   .. code-block:: bash

      docker build -t ai-document-chat .

2. Run the container:

   .. code-block:: bash

      docker run -p 5000:5000 ai-document-chat

Next Steps
----------

- :ref:`User Guide <user-guide>` - Learn how to use the application
- :ref:`API Reference <api>` - Explore the API documentation
- :ref:`Development <development>` - Contribute to the project
