# Financial RAG System - Backend

FastAPI-based backend for the Financial Reports RAG System with flexible, configurable LLM and embedding providers.

## Features

- **Flexible LLM Providers**: OpenAI GPT-4, Anthropic Claude, or local models
- **Flexible Embedding Providers**: OpenAI embeddings or local models
- **Vector Database**: Qdrant for semantic search
- **Type-Safe Configuration**: Pydantic Settings with environment variables
- **Structured Logging**: Colored console output and file logging
- **Service Abstractions**: Easy to swap implementations
- **Async Support**: Built on FastAPI with async/await
- **Health Checks**: Detailed service status endpoints

## Quick Start

### 1. Set Up Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

**Required settings:**
- `OPENAI_API_KEY` - Your OpenAI API key (if using OpenAI)
- `QDRANT_HOST` - Qdrant host (default: localhost)

### 3. Start Qdrant (Vector Database)

```bash
# Using Docker
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### 4. Run the Application

```bash
# Run with uvicorn
uvicorn app.main:app --reload

# Or run directly
python -m app.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## Configuration

### LLM Providers

Configure via environment variables in `.env`:

**OpenAI (default):**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

**Anthropic Claude:**
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**Local Model (coming soon):**
```bash
LLM_PROVIDER=local
LOCAL_LLM_MODEL_PATH=/path/to/model
```

### Embedding Providers

**OpenAI (default):**
```bash
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072
```

**Local Embeddings (coming soon):**
```bash
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
LOCAL_EMBEDDING_DIMENSION=768
```

### RAG Configuration

```bash
# Chunking
CHUNK_SIZE=1024
CHUNK_OVERLAP=128
CHUNK_STRATEGY=recursive

# Retrieval
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# Response
MAX_CONTEXT_LENGTH=4000
INCLUDE_SOURCES=True
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py           # Configuration with Pydantic Settings
│   │   └── logging.py          # Logging configuration
│   ├── services/
│   │   ├── base.py             # Abstract service interfaces
│   │   ├── factory.py          # Service factory pattern
│   │   ├── llm/
│   │   │   ├── openai_service.py
│   │   │   └── anthropic_service.py
│   │   ├── embeddings/
│   │   │   └── openai_service.py
│   │   └── vector/
│   │       └── qdrant_service.py
│   └── api/
│       └── routes/             # API endpoints (coming soon)
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
└── README.md                   # This file
```

## API Endpoints

### Health Checks

**Basic Health:**
```bash
GET /health
```

**Detailed Health:**
```bash
GET /health/detailed
```

Returns status of all services:
- LLM service (provider, model)
- Embedding service (provider, model, dimension)
- Vector DB (connection status)
- Collection info (vectors count)

### Coming Soon

- `POST /api/v1/documents/upload` - Upload and process documents
- `POST /api/v1/query` - Query documents with natural language
- `GET /api/v1/documents` - List uploaded documents

## Development

### Testing Configuration

```bash
# Test configuration
python -m app.core.config

# This will print configuration summary
```

### Testing Services

```bash
# Start Python REPL
python

# Test LLM service
from app.services.factory import get_llm_service
from app.services.base import Message

llm = get_llm_service()
messages = [Message(role="user", content="Hello!")]
response = await llm.generate(messages)
print(response.content)

# Test embedding service
from app.services.factory import get_embedding_service

embed = get_embedding_service()
vector = await embed.embed_text("test text")
print(f"Dimension: {len(vector)}")

# Test vector service
from app.services.factory import get_vector_service

vector_db = get_vector_service()
connected = await vector_db.validate_connection()
print(f"Connected: {connected}")
```

### Code Quality

```bash
# Format code
black app/

# Lint code
ruff check app/

# Type check
mypy app/
```

### Running Tests

```bash
# Run tests (coming soon)
pytest

# With coverage
pytest --cov=app tests/
```

## Architecture

### Service Abstraction

All services implement abstract base classes (`BaseLLMService`, `BaseEmbeddingService`, `BaseVectorService`), making it easy to:

1. **Swap providers** without changing client code
2. **Add new providers** by implementing the interface
3. **Test with mocks** by creating test implementations
4. **Configure at runtime** via environment variables

### Factory Pattern

Services are created via factory functions that:

1. Read configuration from settings
2. Instantiate the appropriate service
3. Return the abstract interface
4. Support singleton pattern for shared instances

Example:
```python
from app.services.factory import get_llm_service

# Automatically creates OpenAI or Anthropic based on config
llm = get_llm_service()

# Use the service (provider-agnostic)
response = await llm.generate(messages)
```

### Configuration Management

Uses Pydantic Settings for:

1. **Type safety**: All settings are typed and validated
2. **Environment variables**: Read from `.env` file or environment
3. **Defaults**: Sensible defaults for all settings
4. **Validation**: Automatic validation on startup

## Troubleshooting

### "ModuleNotFoundError"

Make sure virtual environment is activated:
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### "Connection refused" (Qdrant)

Make sure Qdrant is running:
```bash
docker ps  # Check if Qdrant container is running
docker run -p 6333:6333 qdrant/qdrant  # Start Qdrant
```

### "Invalid API key" (OpenAI)

Check that your API key is set in `.env`:
```bash
cat .env | grep OPENAI_API_KEY
```

### Configuration issues

Test configuration:
```bash
python -m app.core.config
```

This will validate and print your configuration.

## Next Steps

Phase 1 (Current):
- [x] Project structure
- [x] Configuration system
- [x] Service abstractions
- [x] LLM services (OpenAI, Anthropic)
- [x] Embedding services (OpenAI)
- [x] Vector DB service (Qdrant)
- [x] FastAPI app with health checks
- [ ] Document upload endpoint
- [ ] PDF processing service
- [ ] Text chunking service
- [ ] RAG query endpoint
- [ ] Complete RAG pipeline

Phase 2:
- [ ] Supabase integration
- [ ] User authentication
- [ ] Async processing (Celery)
- [ ] Document management

Phase 3:
- [ ] Caching (Redis)
- [ ] Testing
- [ ] Deployment
- [ ] Monitoring

## License

MIT
