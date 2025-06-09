.. _development:

Development Guide
================

This guide provides information for developers who want to contribute to the AI Document Chat project.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   development/setup
   development/architecture
   development/coding_standards
   development/testing
   development/api_documentation
   development/release_process

Getting Started
--------------

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see :doc:`development/setup`)
4. Create a new branch for your changes
5. Make your changes and commit them
6. Push your branch to your fork
7. Open a pull request

Development Environment
----------------------

See :doc:`development/setup` for detailed instructions on setting up your development environment.

Project Structure
----------------

.. code-block:: text

   ai-document-chat/
   ├── docs/                   # Documentation
   ├── src/                    # Source code
   │   ├── __init__.py
   │   ├── app.py              # Flask application
   │   ├── chatbot.py          # Chatbot implementation
   │   ├── config.py           # Configuration handling
   │   ├── document_processor.py # Document processing
   │   └── utils/              # Utility functions
   ├── tests/                  # Test suite
   ├── .gitignore
   ├── README.md
   ├── requirements.txt
   └── setup.py

Code Style
----------

We follow the `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python code.

We use the following tools to maintain code quality:

- ``black`` for code formatting
- ``isort`` for import sorting
- ``flake8`` for linting
- ``mypy`` for type checking

Run the following command to check your code before committing:

.. code-block:: bash

   make lint

Testing
-------

We use ``pytest`` for testing. To run the tests:

.. code-block:: bash

   make test

Or to run a specific test:

.. code-block:: bash

   pytest tests/test_module.py::TestClass::test_method

Documentation
------------

Documentation is written in reStructuredText and built using Sphinx.

To build the documentation:

.. code-block:: bash

   make docs

To view the documentation locally:

.. code-block:: bash

   open docs/_build/html/index.html

Pull Requests
------------

1. Fork the repository and create a new branch
2. Make your changes
3. Add tests for your changes
4. Run the test suite and ensure all tests pass
5. Update the documentation if needed
6. Submit a pull request with a clear description of your changes

Code Review
-----------

All pull requests require at least one approval from a maintainer before merging.

Please be responsive to any feedback or requested changes.

Release Process
--------------

See :doc:`development/release_process` for information about the release process.

License
-------

This project is licensed under the MIT License - see the LICENSE file for details.
