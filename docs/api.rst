.. _api:

API Reference
=============

This document provides detailed information about the AI Document Chat API.

.. toctree::
   :maxdepth: 2
   :caption: API Endpoints:

   api/rest_api
   api/websocket_api

Overview
--------

The AI Document Chat provides both REST and WebSocket APIs for interacting with the application programmatically.

Base URL
--------

All API endpoints are relative to the base URL of your application (e.g., ``http://localhost:5000/api/``).

Authentication
--------------

Most API endpoints require authentication. Include your API key in the request headers:

.. code-block:: http

   Authorization: Bearer YOUR_API_KEY

To generate an API key, go to the settings page in the web interface.

Rate Limiting
-------------

API requests are rate-limited to prevent abuse. The current limits are:

- 60 requests per minute per IP address
- 1,000 requests per hour per API key

Response Format
--------------

All API responses are in JSON format and include the following fields:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Field
     - Description
   * - ``status``
     - Either "success" or "error"
   * - ``data``
     - The response data (present on success)
   * - ``message``
     - A human-readable message (present on error)
   * - ``code``
     - An error code (present on error)

Example Response:

.. code-block:: json

   {
     "status": "success",
     "data": {
       "id": "123",
       "name": "Example Document"
     }
   }

Error Handling
-------------

Errors are returned with the appropriate HTTP status code and a JSON response containing error details.

Common HTTP Status Codes:

- ``200 OK``: The request was successful
- ``400 Bad Request``: Invalid request parameters
- ``401 Unauthorized``: Authentication failed
- "404 Not Found": The requested resource was not found
- "429 Too Many Requests": Rate limit exceeded
- "500 Internal Server Error": An unexpected error occurred

Example Error Response:

.. code-block:: json

   {
     "status": "error",
     "message": "Invalid API key",
     "code": "invalid_api_key"
   }

WebSocket API
------------

The WebSocket API provides real-time communication with the application. See the :doc:`WebSocket API <api/websocket_api>` documentation for more details.

REST API Reference
------------------

For detailed information about the available REST API endpoints, see the :doc:`REST API <api/rest_api>` documentation.

API Versioning
-------------

The API is versioned to ensure backward compatibility. The current API version is ``v1``.

Include the API version in the URL path (e.g., ``/api/v1/...``).

Deprecation Policy
------------------

- Endpoints will be marked as deprecated at least one minor version before removal
- Deprecated endpoints will continue to work for at least one major version
- Breaking changes will only be introduced in major version updates

Changelog
---------

See the :doc:`changelog` for a history of API changes.
