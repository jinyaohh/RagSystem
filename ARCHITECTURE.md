# Financial Reports RAG System - Technical Architecture

## Overview
Production-grade RAG (Retrieval-Augmented Generation) system for querying financial reports using natural language.

## System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│                  Next.js + React + TypeScript                │
│              (UI, SSR, Client-side interactions)             │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST/WebSocket API
┌─────────────────────────┴───────────────────────────────────┐
│                      API Gateway Layer                       │
│                      Nginx (Reverse Proxy)                   │
│              (Load balancing, SSL, Rate limiting)            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                      Backend Layer                           │
│                   FastAPI + Python 3.11+                     │
│          (Business logic, RAG orchestration, APIs)           │
└──┬──────────────┬──────────────┬────────────────┬───────────┘
   │              │              │                │
   ▼              ▼              ▼                ▼
┌──────┐   ┌───────────┐   ┌─────────┐   ┌────────────┐
│Vector│   │PostgreSQL │   │  Redis  │   │  AI APIs   │
│  DB  │   │(Metadata) │   │(Cache)  │   │OpenAI/     │
│Qdrant│   │           │   │         │   │Anthropic   │
└──────┘   └───────────┘   └─────────┘   └────────────┘
```

## Tech Stack Details

### 1. Frontend Stack
**Framework: Next.js 14+ (App Router)**
- **Why Next.js over React:**
  - Server-Side Rendering (SSR) for better SEO
  - API routes for backend-for-frontend pattern
  - Built-in optimization (image, fonts, code splitting)
  - Better performance and user experience
  - Easy deployment to Vercel/AWS
  - TypeScript support out of the box

**UI Libraries:**
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: High-quality React components
- **React Query (TanStack Query)**: Server state management
- **Zustand**: Client state management
- **React Hook Form**: Form handling
- **Chart.js / Recharts**: Data visualization for financial metrics

**Key Features:**
- Real-time chat interface for queries
- Document upload interface
- Search history
- Document viewer with highlighting
- Analytics dashboard
- User authentication UI

### 2. Backend Stack
**Framework: FastAPI**
- **Why FastAPI:**
  - Native async/await support (crucial for AI API calls)
  - Automatic OpenAPI documentation
  - Fast performance (similar to Node.js/Go)
  - Type hints and validation with Pydantic
  - WebSocket support for real-time streaming
  - Large Python AI/ML ecosystem

**Core Libraries:**
- **LangChain**: RAG orchestration and prompt management
- **LlamaIndex**: Alternative/complementary to LangChain
- **Pydantic V2**: Data validation and settings
- **SQLAlchemy 2.0**: ORM for PostgreSQL
- **Alembic**: Database migrations
- **Celery**: Async task queue for document processing
- **Redis**: Caching and Celery broker
- **PyJWT**: Authentication tokens

**Document Processing:**
- **PyPDF2/pdfplumber**: PDF extraction
- **python-docx**: Word document processing
- **pandas**: Excel/CSV processing
- **beautifulsoup4**: HTML parsing
- **unstructured**: Multi-format document parsing

**AI/ML Libraries:**
- **OpenAI Python SDK**: GPT-4, embeddings
- **sentence-transformers**: Local embeddings (optional)
- **tiktoken**: Token counting
- **numpy**: Vector operations
- **tenacity**: Retry logic for API calls

### 3. Vector Database
**Choice: Qdrant**
- **Why Qdrant:**
  - Open-source and self-hostable
  - Excellent performance and scalability
  - Rich filtering capabilities (crucial for financial data)
  - Good Python SDK
  - Docker deployment ready
  - Active development and community
  - Supports hybrid search (dense + sparse vectors)

**Alternatives Considered:**
- **Pinecone**: Great but costs money, less control
- **Weaviate**: Good but more complex setup
- **Chroma**: Good for prototyping, less production-ready
- **Milvus**: Enterprise-grade but heavier

**Qdrant Features We'll Use:**
- Collections for different document types
- Payload filtering for metadata
- Hybrid search for better accuracy
- Snapshots for backup
- HNSW index for fast similarity search

### 4. Relational Database
**Choice: PostgreSQL 15+**
- **Purpose:**
  - User management and authentication
  - Document metadata and tracking
  - Query history and analytics
  - System configuration
  - Audit logs

**Schema Design:**
```sql
- users (id, email, hashed_password, created_at)
- documents (id, filename, file_type, upload_date, user_id, status)
- document_chunks (id, document_id, chunk_index, content, vector_id)
- queries (id, user_id, question, answer, created_at, response_time)
- feedback (id, query_id, rating, comment)
```

### 5. Caching Layer
**Choice: Redis 7+**
- **Use Cases:**
  - Cache frequent queries and responses
  - Store user sessions
  - Celery task queue broker
  - Rate limiting data
  - Temporary document processing status

### 6. AI/LLM Services
**Primary: OpenAI**
- **GPT-4-Turbo**: Response generation
- **text-embedding-3-large**: Vector embeddings (3072 dimensions)
- **Fallback**: text-embedding-3-small (1536 dimensions, cheaper)

**Alternative: Anthropic Claude**
- **Claude 3.5 Sonnet**: Excellent for financial analysis
- Can be used alongside or instead of GPT-4

**Embedding Strategy:**
- Batch embeddings during document ingestion
- Cache embeddings in Qdrant
- Use same model for query and document embeddings

### 7. Infrastructure & DevOps

**Containerization:**
- **Docker & Docker Compose**: Development environment
- Multi-stage builds for optimization
- Separate containers for: backend, frontend, qdrant, postgres, redis, nginx

**CI/CD:**
- **GitHub Actions**: Automated testing and deployment
- **Pre-commit hooks**: Code quality (black, ruff, mypy, eslint)

**Monitoring & Logging:**
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Sentry**: Error tracking
- **ELK Stack** (optional): Log aggregation

**Deployment Options:**
1. **Cloud VM** (AWS EC2, DigitalOcean, Linode)
2. **Kubernetes** (for scaling)
3. **Vercel** (frontend) + **Railway/Render** (backend)

### 8. Security

**Authentication & Authorization:**
- JWT tokens with refresh mechanism
- Role-based access control (RBAC)
- OAuth2 with Password Flow
- API key management for service-to-service

**Data Security:**
- HTTPS/TLS encryption
- Environment variables for secrets
- Input sanitization and validation
- SQL injection prevention (SQLAlchemy ORM)
- Rate limiting on APIs
- CORS configuration

**Compliance:**
- Data encryption at rest
- Audit logging
- User data privacy (GDPR considerations)
- Secure file upload validation

## RAG Pipeline Architecture

### Document Ingestion Pipeline
```
Upload → Validation → Parse → Chunk → Embed → Store → Index
   │         │          │       │       │       │       │
   │         │          │       │       │       │       └─→ Update search index
   │         │          │       │       │       └──────────→ Store in Qdrant
   │         │          │       │       └──────────────────→ Generate embeddings (OpenAI)
   │         │          │       └──────────────────────────→ Smart chunking (overlap)
   │         │          └──────────────────────────────────→ Extract text + metadata
   │         └─────────────────────────────────────────────→ File type, size checks
   └───────────────────────────────────────────────────────→ Save file to storage
```

### Query Pipeline
```
Question → Embed → Search → Rerank → Context → Prompt → LLM → Response
    │        │       │         │         │        │       │       │
    │        │       │         │         │        │       │       └─→ Stream to user
    │        │       │         │         │        │       └──────────→ Generate answer
    │        │       │         │         │        └──────────────────→ Construct prompt
    │        │       │         │         └───────────────────────────→ Build context window
    │        │       │         └─────────────────────────────────────→ Rerank results
    │        │       └───────────────────────────────────────────────→ Vector similarity search
    │        └───────────────────────────────────────────────────────→ Convert to embedding
    └────────────────────────────────────────────────────────────────→ Preprocess query
```

### Chunking Strategy
- **Chunk Size**: 512-1024 tokens
- **Overlap**: 128 tokens
- **Strategy**: Semantic chunking (respect paragraphs, sentences)
- **Metadata**: Document ID, page number, section, date

### Retrieval Strategy
- **Hybrid Search**: Dense (vector) + Sparse (BM25)
- **Top-K**: Retrieve 5-10 most relevant chunks
- **Reranking**: Use cross-encoder for better relevance
- **Filtering**: Filter by document type, date range, company

### Prompt Engineering
```
System Prompt: You are a financial analyst assistant...
Context: [Retrieved chunks with metadata]
Question: [User query]
Instructions: Answer based only on the provided context...
```

## Project Structure

```
RagSystem/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── queries.py
│   │   │   │   └── health.py
│   │   │   └── deps.py             # Dependencies
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py         # Auth logic
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py          # DB session
│   │   │   ├── base.py             # Base model
│   │   │   └── models/
│   │   │       ├── user.py
│   │   │       ├── document.py
│   │   │       └── query.py
│   │   ├── schemas/                # Pydantic models
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   └── query.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── rag_service.py      # RAG orchestration
│   │   │   ├── document_service.py # Document processing
│   │   │   ├── embedding_service.py
│   │   │   ├── vector_service.py   # Qdrant operations
│   │   │   └── llm_service.py      # LLM calls
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── document_tasks.py   # Celery tasks
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── chunking.py
│   │       ├── parsers.py
│   │       └── validators.py
│   ├── alembic/                    # Migrations
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── chat/
│   │   │   ├── documents/
│   │   │   └── api/                # API routes
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn components
│   │   │   ├── chat/
│   │   │   ├── documents/
│   │   │   └── layout/
│   │   ├── lib/
│   │   │   ├── api.ts              # API client
│   │   │   ├── utils.ts
│   │   │   └── hooks/
│   │   ├── types/
│   │   └── styles/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── Dockerfile
│
├── docker/
│   ├── nginx/
│   │   └── nginx.conf
│   └── docker-compose.yml
│
├── scripts/
│   ├── setup.sh
│   └── init_db.sql
│
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
│
├── .github/
│   └── workflows/
│       ├── backend-tests.yml
│       └── frontend-tests.yml
│
├── .env.example
├── .gitignore
├── README.md
└── ARCHITECTURE.md                 # This file
```

## Development Workflow

1. **Local Development:**
   ```bash
   docker-compose up -d
   cd backend && uvicorn app.main:app --reload
   cd frontend && npm run dev
   ```

2. **Document Ingestion:**
   - User uploads PDF via frontend
   - Backend validates and saves file
   - Celery task processes document asynchronously
   - Chunks are created and embedded
   - Vectors stored in Qdrant
   - Metadata stored in PostgreSQL
   - User notified of completion

3. **Query Flow:**
   - User enters question in chat
   - Frontend sends to backend API
   - Backend embeds query
   - Searches Qdrant for relevant chunks
   - Retrieves top-K results
   - Constructs prompt with context
   - Calls LLM API (streaming)
   - Streams response to frontend
   - Logs query and response
   - Updates analytics

## Scalability Considerations

1. **Horizontal Scaling:**
   - Multiple FastAPI backend instances
   - Load balancer (Nginx/AWS ALB)
   - Stateless backend design

2. **Caching Strategy:**
   - Redis for frequent queries
   - CDN for frontend assets
   - Embedding cache

3. **Database Optimization:**
   - PostgreSQL connection pooling
   - Qdrant clustering (if needed)
   - Database indexing strategy

4. **Cost Optimization:**
   - Batch embedding calls
   - Cache LLM responses
   - Use smaller models where appropriate
   - Implement rate limiting

## Performance Targets

- **Query Response Time**: < 3 seconds (P95)
- **Document Processing**: < 2 minutes for 50-page PDF
- **Concurrent Users**: 100+ simultaneous
- **Uptime**: 99.9%
- **API Rate Limit**: 100 requests/minute per user

## Future Enhancements

1. **Multi-tenancy**: Support multiple organizations
2. **Advanced Analytics**: User behavior, popular queries
3. **Fine-tuned Models**: Custom embeddings for finance
4. **Multi-modal**: Handle charts, tables, images
5. **Collaborative Features**: Share queries, annotations
6. **Export Features**: Generate reports, export conversations
7. **Integration**: Connect to external data sources (APIs)
8. **Mobile App**: React Native mobile application

## Cost Estimation (Monthly)

**For moderate usage (1000 queries/day, 100 documents):**

- Cloud VM (4 CPU, 16GB RAM): $50-100
- OpenAI API (embeddings + GPT-4): $100-300
- Domain + SSL: $15
- Monitoring (optional): $20-50
- **Total**: ~$200-450/month

**Free Tier Option:**
- Use local embeddings (sentence-transformers)
- Use open-source LLMs (Llama 2, Mistral)
- Deploy on free tiers (Railway, Render free plans)
- Self-host everything

## Conclusion

This architecture provides:
- ✅ Production-grade quality
- ✅ Scalability
- ✅ Maintainability
- ✅ Security
- ✅ Professional for resume
- ✅ Cost-effective
- ✅ Modern tech stack

The combination of FastAPI + Next.js + Qdrant gives you a powerful, performant, and impressive system that demonstrates full-stack capabilities, ML/AI integration, and modern development practices.
