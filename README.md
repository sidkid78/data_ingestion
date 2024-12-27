# Data Ingestion and Processing Pipeline

A scalable data ingestion and processing pipeline for the 4D AI-Driven Knowledge Framework. This system automates the acquisition, transformation, validation, and enrichment of data from various sources, including regulatory documents, academic publications, and industry standards.

## Features

- **Automated Data Acquisition**
  - Federal Register API integration
  - FAR/DFARS document ingestion
  - Support for multiple data sources
  - Configurable update intervals

- **Advanced Processing**
  - NLP-driven metadata enrichment
  - Entity extraction and relationship mapping
  - Citation detection and validation
  - YAML-based document validation

- **Scalable Storage**
  - PostgreSQL for structured data
  - Neo4j for relationship graphs
  - Azure Blob Storage for documents
  - Version control integration

- **Robust Architecture**
  - Asynchronous operations
  - Retry mechanisms
  - Comprehensive logging
  - Error handling

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Neo4j 4.4+
- Azure Storage Account
- Docker and Docker Compose

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sidkid78/data_ingestion_and_processing.git
   cd data_ingestion_and_processing
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install spaCy language model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

6. Update the `.env` file with your configuration:
   ```env
   # Azure Storage
   AZURE_STORAGE_CONNECTION_STRING=your_connection_string

   # PostgreSQL
   POSTGRES_USER=your_postgres_user
   POSTGRES_PASSWORD=your_postgres_password
   POSTGRES_DB=knowledge_db

   # Neo4j
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_neo4j_password

   # API Keys
   FEDERAL_REGISTER_API_KEY=your_api_key
   ```

## Usage

1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. Run the FastAPI application:
   ```bash
   uvicorn src.main:app --reload
   ```

3. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

- `GET /health`: Health check endpoint
- `GET /documents`: List documents with filtering and pagination
- `GET /documents/{document_id}`: Get document details
- `GET /documents/{document_id}/relationships`: Get document relationships
- `POST /ingest/federal-register`: Trigger Federal Register ingestion
- `POST /ingest/far-dfars`: Trigger FAR/DFARS ingestion

## Project Structure

```
project/
├── src/
│   ├── ingestion/          # Data acquisition
│   ├── processing/         # Transformation and validation
│   ├── storage/           # Database connectors
│   └── utils/             # Shared utilities
├── tests/                 # Test suites
├── config/               # Configuration files
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Development

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Check code style:
   ```bash
   black src tests
   isort src tests
   mypy src
   ```

## Configuration

The application is configured through:
- Environment variables (`.env`)
- YAML configuration (`config/app_config.yaml`)
- Command-line arguments

See `config/app_config.yaml` for available options.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Federal Register API
- spaCy for NLP processing
- FastAPI framework
- SQLAlchemy and Neo4j 