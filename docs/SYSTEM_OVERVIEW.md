# System Overview - Financial Reports RAG System

## What is This System?

This is a production-grade **Retrieval-Augmented Generation (RAG)** system that allows users to:

1. **Upload** financial documents (PDFs, DOCX, Excel files)
2. **Ask questions** in natural language about those documents
3. **Get accurate answers** with citations to source material
4. **Manage** their document library
5. **Track** query history and analytics

Think of it as "ChatGPT for your financial reports" - but the AI only answers based on YOUR uploaded documents, not general knowledge.

## How Does RAG Work?

```
Traditional AI Problem:
❌ LLMs don't know about YOUR specific documents
❌ LLMs can hallucinate (make up facts)
❌ No way to verify answers

RAG Solution:
✅ Converts your documents into searchable vectors
✅ Finds relevant information from YOUR documents
✅ Provides that information to the LLM as context
✅ LLM answers based ONLY on provided context
✅ Includes citations for verification
```

## System Flow Diagram

### Document Upload Flow

```
┌─────────────┐
│   User      │
│ Uploads PDF │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│   Frontend       │
│  (Next.js)       │
└──────┬───────────┘
       │ HTTP POST /api/documents/upload
       ▼
┌──────────────────┐
│   Backend API    │──────┐ Save file metadata
│  (FastAPI)       │      │
└──────┬───────────┘      ▼
       │            ┌──────────────┐
       │ Trigger    │ PostgreSQL   │
       │ Async Job  │  (Metadata)  │
       ▼            └──────────────┘
┌──────────────────┐
│  Celery Worker   │
│ (Background Task)│
└──────┬───────────┘
       │
       ▼
┌────────────────────────────────────┐
│  Document Processing Pipeline      │
│  1. Parse PDF (extract text)       │
│  2. Split into chunks (1024 tokens)│
│  3. Generate embeddings (OpenAI)   │
│  4. Store vectors (Qdrant)         │
│  5. Update status (PostgreSQL)     │
└────────────────────────────────────┘
       │
       ▼
   [Document Ready for Querying]
```

### Query Flow

```
┌─────────────┐
│   User      │
│Asks Question│
└──────┬──────┘
       │ "What was the Q4 revenue?"
       ▼
┌──────────────────┐
│   Frontend       │
│  (Chat UI)       │
└──────┬───────────┘
       │ WebSocket / HTTP POST /api/query
       ▼
┌──────────────────┐
│   Backend API    │
│  (RAG Service)   │
└──────┬───────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Step 1: Convert Question to Vector    │
│  "What was Q4 revenue?"                │
│  ──────▶ OpenAI Embeddings API         │
│  ──────▶ [0.123, 0.456, ..., 0.789]   │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  Step 2: Search Similar Chunks         │
│  Query Qdrant with embedding vector    │
│  ──────▶ Returns top 5 relevant chunks │
│                                         │
│  Results:                              │
│  • "Q4 revenue was $150M..." (95%)     │
│  • "Revenue breakdown by..." (87%)     │
│  • "Compared to Q3 revenue..." (82%)   │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  Step 3: Build Context                 │
│  Combine retrieved chunks:             │
│                                         │
│  Context:                              │
│  Document: Annual Report 2023, Page 5  │
│  Content: "Q4 revenue was $150M..."    │
│                                         │
│  Document: Annual Report 2023, Page 12 │
│  Content: "Revenue breakdown by..."    │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  Step 4: Construct Prompt              │
│                                         │
│  System: You are a financial analyst   │
│  Context: [Retrieved chunks above]     │
│  Question: What was the Q4 revenue?    │
│  Instructions: Answer based only on    │
│  the provided context. Cite sources.   │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  Step 5: Call LLM                      │
│  Send to OpenAI GPT-4                  │
│  ──────▶ Receive streaming response    │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  Step 6: Stream Response to User       │
│                                         │
│  Answer: "According to the Annual      │
│  Report 2023 (page 5), the Q4 revenue  │
│  was $150 million, representing a 12%  │
│  increase from Q3..."                  │
│                                         │
│  Sources:                              │
│  • Annual Report 2023, Page 5          │
│  • Annual Report 2023, Page 12         │
└────────────────┬───────────────────────┘
                 │
                 ▼
           ┌─────────────┐
           │   User      │
           │ Sees Answer │
           └─────────────┘
```

## Component Breakdown

### 1. Frontend (Next.js)

**Purpose**: User interface

**Features**:
- Document upload interface
- Chat interface for asking questions
- Document library management
- User authentication
- Real-time streaming responses
- Analytics dashboard

**Tech**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui

### 2. Backend API (FastAPI)

**Purpose**: Business logic orchestration

**Responsibilities**:
- Handle HTTP requests
- User authentication (JWT)
- Coordinate RAG pipeline
- Manage database operations
- API documentation (auto-generated)

**Endpoints**:
- `POST /api/v1/documents/upload` - Upload documents
- `POST /api/v1/query` - Ask questions
- `GET /api/v1/documents` - List documents
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/health` - Health check

### 3. PostgreSQL Database

**Purpose**: Structured data storage

**Stores**:
- User accounts and authentication
- Document metadata (filename, upload date, status)
- Query history
- Feedback and ratings
- System configuration

**Why PostgreSQL?**
- Reliable, production-grade
- ACID compliance
- JSON support for flexible schemas
- Full-text search capabilities
- pgvector extension available if needed

### 4. Qdrant Vector Database

**Purpose**: Semantic search engine

**Stores**:
- Document embeddings (vector representations)
- Chunk text and metadata
- Enables similarity search

**How it works**:
1. Document chunks → OpenAI Embeddings → Vectors (3072 dimensions)
2. Store vectors in Qdrant with metadata (document ID, page, etc.)
3. Query → Embedding → Find similar vectors → Return relevant chunks

**Why Qdrant?**
- Fast similarity search
- Rich metadata filtering
- Hybrid search (dense + sparse)
- Production-ready, scalable

### 5. Redis Cache

**Purpose**: Performance optimization

**Uses**:
- Cache frequent query responses
- Store user sessions
- Celery task queue broker
- Rate limiting counters
- Temporary data storage

**Benefits**:
- Faster response times (no need to re-query LLM)
- Reduced API costs
- Better user experience

### 6. Celery Worker

**Purpose**: Background task processing

**Tasks**:
- Document parsing (PDF → text extraction)
- Text chunking
- Embedding generation (can take minutes for large docs)
- Vector storage
- Cleanup jobs

**Why async?**
- Don't block API responses
- User gets immediate feedback
- Process large documents without timeout
- Better resource utilization

### 7. OpenAI API

**Purpose**: AI intelligence

**Services Used**:
- **GPT-4 Turbo**: Generate answers to questions
- **text-embedding-3-large**: Convert text to vectors

**Why OpenAI?**
- State-of-the-art quality
- Reliable API
- Good documentation
- Reasonable pricing

### 8. Nginx Reverse Proxy

**Purpose**: Traffic management

**Functions**:
- Load balancing
- SSL/TLS termination
- Static file serving
- Rate limiting
- Request routing

## Data Flow Example

Let's trace a complete user journey:

### Scenario: User uploads a 10-K filing and asks about revenue

**1. Document Upload (Day 1)**

```
User uploads "AAPL_10K_2023.pdf" (50 pages)
  ↓
Frontend sends file to backend
  ↓
Backend saves file, creates DB entry (status: processing)
  ↓
Returns immediately to user: "Document uploaded, processing..."
  ↓
Celery task starts in background:
  - Extract text from PDF (50 pages → ~25,000 words)
  - Split into chunks (25,000 words → ~25 chunks of 1024 tokens)
  - Generate embeddings (25 chunks → 25 API calls to OpenAI)
  - Store in Qdrant (25 vectors with metadata)
  - Update DB (status: ready)
  ↓
User sees notification: "Document ready!"
```

**2. First Query (5 minutes later)**

```
User asks: "What was Apple's total revenue in 2023?"
  ↓
Frontend sends question to backend
  ↓
Backend RAG service:
  1. Embed question → [0.234, 0.567, ...]
  2. Search Qdrant → finds 5 relevant chunks
     • Chunk from page 15: "Total revenue $394B..."
     • Chunk from page 23: "Revenue by segment..."
     • etc.
  3. Build prompt with context
  4. Call GPT-4 with streaming
  5. Stream response back to user
  ↓
User sees answer appear word-by-word:
"According to Apple's 10-K filing for 2023 (page 15),
total revenue was $394.3 billion..."

[Sources: AAPL_10K_2023.pdf, pages 15, 23, 34]
```

**Time**: ~3 seconds from question to complete answer

**3. Second Query (same question, 1 minute later)**

```
User asks same question again (testing)
  ↓
Backend checks Redis cache
  ↓
Cache HIT! Return cached response immediately
  ↓
User sees answer in <100ms (30x faster!)
```

**Cost saved**: No OpenAI API call needed

## Performance Characteristics

### Document Processing

| Document Size | Processing Time | API Cost |
|--------------|-----------------|----------|
| 10 pages     | ~30 seconds     | ~$0.05   |
| 50 pages     | ~2 minutes      | ~$0.25   |
| 200 pages    | ~8 minutes      | ~$1.00   |

### Query Response

| Scenario           | Response Time | API Cost |
|-------------------|---------------|----------|
| First query       | 2-4 seconds   | ~$0.02   |
| Cached query      | <100ms        | $0.00    |
| Complex query     | 4-6 seconds   | ~$0.05   |
| Streaming started | <500ms        | -        |

### Concurrent Users

| Users | Response Time | Notes                    |
|-------|---------------|--------------------------|
| 1-10  | Normal        | No degradation           |
| 10-50 | Normal        | Redis cache helps        |
| 50+   | May slow      | Consider scaling         |

## Scaling Considerations

### Vertical Scaling (Increase Server Resources)

**When**: 10-50 concurrent users
- Upgrade to larger VM (more CPU/RAM)
- Cost: $50-200/month

### Horizontal Scaling (Multiple Servers)

**When**: 50+ concurrent users
- Multiple backend API instances behind load balancer
- Separate Celery workers for document processing
- Database connection pooling
- Cost: $200-500/month

### Optimization Strategies

1. **Caching**:
   - Cache frequent queries in Redis
   - Reduces API costs by 60-80%

2. **Batch Processing**:
   - Batch embedding calls (up to 100 at once)
   - Saves API costs and time

3. **Smart Chunking**:
   - Larger chunks = fewer embeddings = lower cost
   - But: may reduce accuracy
   - Sweet spot: 1024 tokens

4. **Model Selection**:
   - Use GPT-4 Turbo (cheaper than GPT-4)
   - Use text-embedding-3-small (cheaper, slightly lower quality)
   - Potential savings: 50%

## Security Architecture

### Authentication Flow

```
User login → Backend validates → Returns JWT token
                                        ↓
User makes request with JWT → Backend validates → Allow/Deny
                                        ↓
                                 Token expires after 30 min
                                        ↓
                                 Refresh token used
```

### Security Measures

1. **Authentication**: JWT tokens with expiry
2. **Authorization**: Role-based access control
3. **Input Validation**: Pydantic models validate all inputs
4. **SQL Injection**: Protected by SQLAlchemy ORM
5. **XSS Protection**: React escapes output by default
6. **File Upload**: Type checking, size limits, virus scanning
7. **Rate Limiting**: Prevent abuse
8. **HTTPS**: Encrypted communication (production)
9. **Secrets Management**: Environment variables, never in code
10. **Audit Logging**: Track all actions

## Cost Breakdown

### Monthly Costs (1000 queries/day, 100 documents)

| Component          | Cost      | Notes                    |
|-------------------|-----------|--------------------------|
| Cloud VM          | $50-100   | 4 CPU, 16GB RAM         |
| OpenAI API        | $100-300  | Depends on usage        |
| Domain & SSL      | $15       | Annual / 12             |
| Monitoring        | $0-50     | Optional (Sentry, etc.) |
| **Total**         | **$165-465** | Average ~$250/month  |

### Cost Optimization

**Free Tier Options**:
- Railway.app: Free tier for backend
- Vercel: Free tier for frontend
- Qdrant Cloud: Free tier (1GB)
- Total: ~$100/month (just OpenAI API)

**DIY Hosting**:
- Home server / old laptop
- Free compute
- Cost: ~$20/month (just OpenAI API)

## Why This Architecture?

### Business-Level Quality

✅ **Scalable**: Can handle growth from 1 to 1000+ users
✅ **Reliable**: Proper error handling, retries, logging
✅ **Maintainable**: Clean code structure, documentation
✅ **Secure**: Industry-standard security practices
✅ **Observable**: Monitoring, logging, metrics
✅ **Testable**: Unit tests, integration tests
✅ **Deployable**: Docker, CI/CD ready

### Resume Value

Shows expertise in:
- Full-stack development (frontend + backend)
- Modern web technologies (Next.js, FastAPI)
- AI/ML integration (OpenAI, RAG)
- Database design (SQL + Vector DB)
- DevOps (Docker, microservices)
- Production practices (caching, async, monitoring)

### Learning Opportunities

- RAG architecture
- Vector databases
- Async programming
- API design
- React/Next.js
- Python/FastAPI
- Docker orchestration
- Production deployment

## Next Steps

1. **Get Started**: Follow [Quick Start Guide](./QUICK_START.md)
2. **Understand Architecture**: Read [Architecture Details](../ARCHITECTURE.md)
3. **Compare Technologies**: See [Tech Stack Comparison](./TECH_STACK_COMPARISON.md)
4. **Deploy**: Check [Deployment Guide](./DEPLOYMENT.md)

## Questions?

- **How does it differ from ChatGPT?** It only uses YOUR documents, not general knowledge
- **Can I use it offline?** No, it requires OpenAI API (or use local LLMs)
- **How accurate is it?** Very accurate, as it quotes directly from documents
- **Can it handle images/charts?** Not yet (future enhancement)
- **What file types?** PDF, DOCX, XLSX, TXT, CSV
- **How many documents?** Unlimited (limited by storage/cost)
- **Is it secure?** Yes, with proper deployment configuration

Ready to build? Let's go! 🚀
