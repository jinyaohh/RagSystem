# CLAUDE.md - Developer & Maintainer Guide

**For:** Developers, maintainers, and contributors
**Version:** 3.0 (Phase 3 - Analytics)
**Last Updated:** November 2025

This guide helps you understand, maintain, and enhance the Financial RAG System.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Codebase Structure](#codebase-structure)
4. [Key Components](#key-components)
5. [Adding New Features](#adding-new-features)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)
10. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### System Phases

The system has three progressive phases:

**Phase 1 (MVP):** Single-user, synchronous processing
- Direct file system storage
- Immediate processing
- No authentication
- Qdrant for vectors

**Phase 2 (Production):** Multi-user, async processing
- Supabase (PostgreSQL) for metadata
- Supabase Storage for files
- JWT authentication
- Celery + Redis for async tasks
- Row-level security (RLS)

**Phase 3 (Analytics):** Advanced insights
- Query logging to database
- Analytics dashboard with Recharts
- Activity tracking
- Performance monitoring

### Technology Stack

**Backend:**
- FastAPI - Web framework
- LangChain - RAG orchestration
- Qdrant - Vector database
- Supabase - PostgreSQL + Auth + Storage
- Celery - Task queue
- Redis - Message broker
- OpenAI - LLM and embeddings

**Frontend:**
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- shadcn/ui - UI components
- Recharts - Data visualization

### Data Flow

```
User Upload → FastAPI → Supabase Storage
                ↓
            Create Job Record (Supabase DB)
                ↓
            Queue Celery Task (Redis)
                ↓
         Celery Worker Processes:
            1. Extract text from file
            2. Chunk text
            3. Generate embeddings (OpenAI)
            4. Store vectors (Qdrant)
            5. Update job status
                ↓
         Document Ready for Querying

User Query → FastAPI → RAG Service
                ↓
          Retrieve vectors (Qdrant)
                ↓
          Generate answer (OpenAI)
                ↓
          Log query (Analytics)
                ↓
          Return answer + sources
```

### Database Schema

**Core Tables:**
- `auth.users` - User accounts (Supabase Auth)
- `documents` - Document metadata
- `document_chunks` - Text chunks metadata
- `processing_jobs` - Async job tracking
- `user_settings` - User preferences
- `user_stats` - Aggregated user statistics

**Analytics Tables:**
- `query_logs` - All user queries
- `system_metrics` - System-wide metrics
- `processing_analytics` - Processing performance

**Views:**
- `user_activity_30d` - Recent activity aggregations
- `processing_performance_by_step` - Performance by step
- `query_stats_by_user` - Per-user query stats

---

## Development Setup

### Prerequisites

```bash
# System requirements
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

# Accounts needed
- OpenAI API key
- Supabase project (for Phase 2+)
```

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/RagSystem.git
cd RagSystem

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies

# Install pre-commit hooks
pre-commit install

# Frontend setup
cd ../frontend
npm install

# Start Docker services
docker-compose up -d
```

### Environment Configuration

Create `.env` files from examples:

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your credentials

# Frontend
cd frontend
cp .env.example .env.local
# Edit .env.local with your configuration
```

### Running Development Servers

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Celery Worker (if Phase 2+)
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Accessing Services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Qdrant: http://localhost:6333/dashboard
- Redis: localhost:6379

---

## Codebase Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py          # Settings management
│   │   └── logging.py         # Logging configuration
│   ├── api/
│   │   └── routes/
│   │       ├── documents.py   # Document upload/management
│   │       ├── query.py       # RAG queries
│   │       ├── auth.py        # Authentication
│   │       ├── jobs.py        # Job tracking
│   │       └── analytics.py   # Analytics endpoints
│   ├── services/
│   │   ├── rag.py            # RAG service (core logic)
│   │   ├── document_processor.py  # Document processing
│   │   ├── supabase_service.py    # Supabase operations
│   │   └── analytics_service.py   # Analytics logic
│   ├── models/
│   │   ├── document.py        # Document models
│   │   ├── user.py           # User models
│   │   ├── job.py            # Job models
│   │   └── analytics.py      # Analytics models
│   ├── middleware/
│   │   └── auth.py           # JWT auth middleware
│   ├── tasks/
│   │   ├── celery_app.py     # Celery configuration
│   │   └── document_tasks.py  # Async processing tasks
│   └── utils/
│       ├── document.py        # Document utilities
│       └── vector.py         # Vector operations
├── tests/                     # Unit and integration tests
├── supabase_schema.sql       # Phase 2 database schema
├── supabase_analytics_schema.sql  # Phase 3 analytics schema
├── requirements.txt          # Python dependencies
└── docker-compose.yml        # Docker services
```

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx        # Root layout
│   │   ├── page.tsx          # Home page
│   │   ├── upload/           # Upload page
│   │   ├── chat/             # Chat interface
│   │   ├── documents/        # Document management
│   │   ├── jobs/             # Job tracking
│   │   ├── analytics/        # Analytics dashboard
│   │   ├── login/            # Login page
│   │   └── signup/           # Signup page
│   ├── components/
│   │   └── ui/               # shadcn/ui components
│   ├── contexts/
│   │   └── AuthContext.tsx   # Authentication context
│   ├── lib/
│   │   ├── api.ts            # API client
│   │   └── utils.ts          # Utility functions
│   └── types/
│       └── index.ts          # TypeScript types
├── public/                   # Static assets
└── package.json             # npm dependencies
```

---

## Key Components

### 1. RAG Service (`backend/app/services/rag.py`)

Core RAG functionality:

```python
class RAGService:
    """Handles retrieval-augmented generation."""

    async def query(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> Dict:
        """Execute RAG query."""
        # 1. Generate embedding for question
        # 2. Search Qdrant for similar chunks
        # 3. Format context from retrieved chunks
        # 4. Generate answer with LLM
        # 5. Return answer with sources
```

**Key methods:**
- `query()` - Main RAG pipeline
- `multi_query()` - Batch processing
- `summarize_document()` - Document summarization
- `compare_documents()` - Document comparison

### 2. Document Processor (`backend/app/services/document_processor.py`)

Handles document processing:

```python
class DocumentProcessor:
    """Process documents into chunks and embeddings."""

    async def process_document(
        self,
        file_path: str,
        document_id: str,
        user_id: str
    ):
        """Process document through pipeline."""
        # 1. Extract text (PDF/DOCX/XLSX/TXT)
        # 2. Chunk text with overlap
        # 3. Generate embeddings for each chunk
        # 4. Store in Qdrant
        # 5. Update database
```

**Extractors:**
- `PDFExtractor` - pypdf for PDF files
- `DOCXExtractor` - python-docx for Word files
- `XLSXExtractor` - openpyxl for Excel files
- `TextExtractor` - Direct text reading

### 3. Analytics Service (`backend/app/services/analytics_service.py`)

Analytics data collection and aggregation:

```python
class AnalyticsService:
    """Handle analytics operations."""

    async def log_query(self, query_log: QueryLogCreate):
        """Log a query for analytics."""

    async def get_user_stats(
        self,
        user_id: UUID,
        days: int = 30
    ) -> UserAnalyticsStats:
        """Get user statistics."""
```

**Key features:**
- Query logging (automatic on every query)
- User statistics aggregation
- Activity tracking (daily queries/uploads)
- Popular queries analysis

### 4. Celery Tasks (`backend/app/tasks/document_tasks.py`)

Async processing:

```python
@celery_app.task(bind=True)
def process_document_async(self, document_id: str, user_id: str):
    """Async document processing task."""

    # Update status to 'processing'
    # Execute processing pipeline
    # Update progress at each step
    # Handle errors gracefully
    # Update final status
```

**Progress tracking:**
- Extraction: 25%
- Chunking: 50%
- Embedding: 75%
- Storage: 100%

### 5. Authentication Middleware (`backend/app/middleware/auth.py`)

JWT-based authentication:

```python
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional)
) -> Optional[User]:
    """Get current user if authenticated."""

    # Verify JWT token
    # Decode user_id
    # Fetch user from Supabase
    # Return User or None
```

**Functions:**
- `get_current_user()` - Required auth
- `get_current_user_optional()` - Optional auth
- `verify_token()` - Token validation

---

## Adding New Features

### Adding a New API Endpoint

1. **Define model** (`backend/app/models/`)
```python
# backend/app/models/mymodel.py
from pydantic import BaseModel

class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    result: str
    status: str
```

2. **Create route** (`backend/app/api/routes/`)
```python
# backend/app/api/routes/myroute.py
from fastapi import APIRouter, Depends
from app.models.mymodel import MyRequest, MyResponse
from app.middleware.auth import get_current_user_optional

router = APIRouter(prefix="/myroute", tags=["MyRoute"])

@router.post("/", response_model=MyResponse)
async def my_endpoint(
    request: MyRequest,
    current_user = Depends(get_current_user_optional)
):
    # Your logic here
    return MyResponse(result="success", status="ok")
```

3. **Register router** (`backend/app/main.py`)
```python
from app.api.routes import myroute

app.include_router(myroute.router, prefix="/api/v1")
```

4. **Add tests** (`backend/tests/`)
```python
# backend/tests/test_myroute.py
def test_my_endpoint(client):
    response = client.post("/api/v1/myroute/", json={
        "field1": "value",
        "field2": 42
    })
    assert response.status_code == 200
    assert response.json()["result"] == "success"
```

### Adding a New Frontend Page

1. **Create page** (`frontend/src/app/mypage/page.tsx`)
```tsx
'use client'

import { useAuth } from '@/contexts/AuthContext'

export default function MyPage() {
  const { isAuthenticated } = useAuth()

  return (
    <div>
      <h1>My New Page</h1>
      {/* Your content */}
    </div>
  )
}
```

2. **Add navigation link** (`frontend/src/app/layout.tsx`)
```tsx
<Link href="/mypage">
  <Button variant="ghost">My Page</Button>
</Link>
```

3. **Create API function** (`frontend/src/lib/api.ts`)
```tsx
export async function getMyData(): Promise<MyData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/myroute/`, {
    headers: getAuthHeaders()
  })
  return handleResponse(response)
}
```

4. **Add TypeScript types** (`frontend/src/types/index.ts`)
```tsx
export interface MyData {
  field1: string
  field2: number
}
```

### Adding a New Analytics Metric

1. **Update analytics schema** (`backend/supabase_analytics_schema.sql`)
```sql
-- Add new column to query_logs
ALTER TABLE query_logs
ADD COLUMN my_metric INTEGER DEFAULT 0;

-- Create index for performance
CREATE INDEX idx_query_logs_my_metric
ON query_logs(my_metric);
```

2. **Update analytics model** (`backend/app/models/analytics.py`)
```python
class QueryLogCreate(BaseModel):
    # ... existing fields
    my_metric: Optional[int] = None
```

3. **Log metric** (`backend/app/api/routes/query.py`)
```python
query_log = QueryLogCreate(
    # ... existing fields
    my_metric=calculated_value
)
await analytics.log_query(query_log)
```

4. **Add to dashboard** (`frontend/src/app/analytics/page.tsx`)
```tsx
// Fetch and display the new metric
const myMetricValue = stats?.my_metric || 0
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_rag.py

# Run specific test
pytest tests/test_rag.py::test_query_success
```

**Test structure:**
```python
# tests/test_myfeature.py
import pytest
from app.services.myservice import MyService

@pytest.fixture
def my_service():
    return MyService()

def test_my_function(my_service):
    result = my_service.my_function("input")
    assert result == "expected_output"

@pytest.mark.asyncio
async def test_async_function(my_service):
    result = await my_service.async_function()
    assert result is not None
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test
npm test -- MyComponent.test.tsx
```

**Test example:**
```tsx
// components/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### Integration Tests

```bash
# Run integration tests (backend + frontend + services)
cd backend
pytest tests/integration/
```

### Test Coverage Goals

- Backend: > 80%
- Frontend: > 70%
- Critical paths: 100%

---

## Deployment

### Production Checklist

**Environment:**
- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong JWT secret
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Enable rate limiting
- [ ] Configure proper logging

**Database:**
- [ ] Run all migrations
- [ ] Set up backups
- [ ] Configure connection pooling
- [ ] Enable RLS policies
- [ ] Create indexes

**Security:**
- [ ] Review security headers
- [ ] Enable HTTPS only
- [ ] Configure CSP
- [ ] Set up monitoring
- [ ] Enable audit logging

### Docker Deployment

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Scaling

**Horizontal Scaling:**
```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3

  celery:
    deploy:
      replicas: 5
```

**Load Balancing:**
- Use Nginx for load balancing
- Configure health checks
- Enable sticky sessions (if needed)

---

## Troubleshooting

### Common Issues

**"ImportError: No module named 'app'"**
```bash
# Solution: Ensure you're in the backend directory
cd backend
source venv/bin/activate
python -m pytest
```

**Qdrant connection refused**
```bash
# Check if Qdrant is running
docker-compose ps qdrant

# Restart Qdrant
docker-compose restart qdrant
```

**Celery tasks not processing**
```bash
# Check Celery worker is running
ps aux | grep celery

# Check Redis connection
docker-compose logs redis

# Restart Celery worker
celery -A app.tasks.celery_app worker --loglevel=debug
```

**Frontend build errors**
```bash
# Clear cache and rebuild
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

### Debugging

**Backend:**
```python
# Add debug logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Debug info: {variable}")

# Use pdb debugger
import pdb; pdb.set_trace()
```

**Frontend:**
```tsx
// Console logging
console.log('Debug:', data)

// React DevTools
// Install React DevTools browser extension
```

### Performance Profiling

**Backend:**
```python
# Add timing decorator
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

**Frontend:**
```tsx
// Use React Profiler
import { Profiler } from 'react'

<Profiler id="MyComponent" onRender={onRenderCallback}>
  <MyComponent />
</Profiler>
```

---

## Contributing

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
git add .
git commit -m "Add my feature"

# Push to remote
git push origin feature/my-feature

# Create pull request on GitHub
```

### Commit Message Format

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Example:**
```
feat(analytics): add custom date range selector

- Add date picker component
- Update analytics API to accept date range
- Add frontend state management for date range

Closes #123
```

### Code Style

**Backend (Python):**
- Follow PEP 8
- Use type hints
- Max line length: 100
- Use Black formatter
- Run `flake8` before committing

**Frontend (TypeScript):**
- Follow Airbnb style guide
- Use ESLint
- Use Prettier formatter
- Prefer functional components
- Use TypeScript strict mode

### Pull Request Process

1. Create descriptive PR title
2. Fill out PR template
3. Link related issues
4. Ensure CI passes
5. Request review
6. Address feedback
7. Squash commits before merge

---

## Future Enhancements

### Planned Features

**Phase 4 - Advanced Features:**
- [ ] Document collaboration and sharing
- [ ] Real-time collaborative queries
- [ ] Custom model fine-tuning
- [ ] Multi-modal support (images, charts)
- [ ] Mobile application

**Analytics Enhancements:**
- [ ] Export analytics to CSV/PDF
- [ ] Custom date range selection
- [ ] Scheduled email reports
- [ ] Anomaly detection
- [ ] Predictive analytics

**Performance:**
- [ ] Query result caching
- [ ] Lazy loading for large documents
- [ ] Pagination for document lists
- [ ] WebSocket for real-time updates
- [ ] CDN for static assets

**Security:**
- [ ] Two-factor authentication
- [ ] API rate limiting per user
- [ ] Document encryption at rest
- [ ] Audit logging
- [ ] GDPR compliance tools

### Architecture Improvements

**Microservices:**
- Separate RAG service
- Dedicated analytics service
- Independent scaling

**Database:**
- Read replicas for scaling
- Materialized views for analytics
- Partitioning for large tables

**Caching:**
- Redis for query results
- CDN for frontend
- In-memory caching for embeddings

---

## Additional Resources

**Documentation:**
- [Phase 2 Setup](docs/setup/PHASE2_PRODUCTION.md)
- [Phase 3 Setup](docs/setup/PHASE3_ANALYTICS.md)
- [Architecture](docs/architecture/ARCHITECTURE.md)
- [API Reference](docs/guides/QUICK_REFERENCE.md)

**External Resources:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangChain Docs](https://python.langchain.com/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Supabase Docs](https://supabase.com/docs)
- [Next.js Docs](https://nextjs.org/docs)

**Community:**
- GitHub Issues - Bug reports and feature requests
- Discussions - Questions and ideas
- Wiki - Community documentation

---

**Last Updated:** November 2025
**Maintainers:** Development Team
**License:** MIT
