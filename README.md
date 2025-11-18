# Financial Reports RAG System

A production-grade Retrieval-Augmented Generation (RAG) system for querying financial reports using natural language. Built with FastAPI, Next.js, Qdrant vector database, and Supabase.

## 🚀 Phase 2: Production-Ready Multi-User System

This system includes two deployment modes:

- **Phase 1 (MVP)**: Single-user system with synchronous processing - perfect for quick setup and testing
- **Phase 2 (Production)**: Multi-user system with authentication, async processing, and job tracking - production-ready

👉 **See [PHASE2_SETUP.md](PHASE2_SETUP.md) for Phase 2 setup guide**

## Features

### Core Features
- **Intelligent Document Processing**: Upload and process financial reports (PDF, DOCX, Excel)
- **Natural Language Queries**: Ask questions about your financial documents in plain English
- **Semantic Search**: Advanced vector search with hybrid retrieval for accurate results
- **Real-time Streaming**: Get answers streamed in real-time as they're generated
- **Document Management**: Track, organize, and manage uploaded documents
- **Citation Support**: Responses include references to source documents

### Phase 2 Features (Production)
- **User Authentication**: Secure JWT-based authentication with Supabase
- **Async Processing**: Background document processing with Celery and Redis
- **Job Tracking**: Real-time monitoring of processing jobs with progress updates
- **User Isolation**: Row-level security ensuring data privacy
- **Scalable Architecture**: Horizontally scalable with distributed task processing
- **Cloud Storage**: Supabase storage for document files
- **Multi-tenancy**: Full support for multiple users with isolated data

## Tech Stack

### Backend
- **FastAPI**: Modern, fast Python web framework
- **LangChain**: RAG orchestration and prompt management
- **Qdrant**: Vector database for semantic search
- **Supabase**: PostgreSQL database with built-in auth and storage (Phase 2)
- **Redis**: Message broker and caching (Phase 2)
- **Celery**: Distributed asynchronous task processing (Phase 2)
- **OpenAI API**: GPT-4 for generation, embeddings for vectors

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: High-quality UI components
- **React Query**: Server state management
- **Zustand**: Client state management

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy and load balancing
- **GitHub Actions**: CI/CD pipeline

## Prerequisites

### Phase 1 (MVP)
- **Docker & Docker Compose**: For containerized development
- **Node.js 18+**: For frontend development
- **Python 3.11+**: For backend development
- **OpenAI API Key**: For embeddings and LLM
- **Git**: Version control

### Phase 2 (Production) - Additional Requirements
- **Supabase Account**: Free tier is sufficient for development
- **Redis**: Included in Docker Compose setup
- All Phase 1 prerequisites

## Quick Start

### Phase 1 (MVP) - Quick Setup

Perfect for testing and development without authentication:

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/RagSystem.git
cd RagSystem
```

#### 2. Environment Setup
```bash
# Backend
cd backend
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
# Set AUTH_ENABLED=false, CELERY_ENABLED=false

# Frontend
cd ../frontend
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3. Start Backend Services
```bash
cd backend
docker-compose up -d qdrant  # Start only Qdrant
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

#### 5. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### Phase 2 (Production) - Full Setup

For production deployment with authentication and async processing:

👉 **See [PHASE2_SETUP.md](PHASE2_SETUP.md) for complete Phase 2 setup instructions**

Quick summary:
1. Create Supabase project and execute schema
2. Configure environment variables (Supabase, Redis, Celery)
3. Start all services with `docker-compose up -d`
4. Start backend and frontend
5. Sign up at http://localhost:3000/signup

## Development Setup

### Backend Development
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
RagSystem/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── tests/        # Backend tests
│   └── alembic/      # Database migrations
├── frontend/         # Next.js frontend
│   └── src/          # Source code
├── docker/           # Docker configurations
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Usage

### Uploading Documents
1. Navigate to the Documents page
2. Click "Upload Document"
3. Select your financial report (PDF, DOCX, or XLSX)
4. Wait for processing to complete
5. Document is now searchable

### Asking Questions
1. Go to the Chat interface
2. Type your question about the financial reports
3. Get AI-powered answers with citations
4. View source documents for verification

### Example Questions
- "What was the total revenue in Q4 2023?"
- "Compare the profit margins between 2022 and 2023"
- "What are the main risk factors mentioned in the report?"
- "Summarize the CEO's letter to shareholders"

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**Phase 1 Endpoints:**
- `POST /api/v1/documents/upload` - Upload a document
- `POST /api/v1/documents/upload-and-process` - Upload and process (sync)
- `POST /api/v1/query/` - Ask a question
- `GET /api/v1/documents/` - List all documents
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/detailed` - Detailed health check

**Phase 2 Additional Endpoints:**
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/jobs/` - List processing jobs
- `GET /api/v1/jobs/{job_id}` - Get job status
- `POST /api/v1/jobs/{job_id}/cancel` - Cancel job

## Configuration

### Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all available configuration options.

**Phase 1 Required:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `AUTH_ENABLED=false`: Disable authentication
- `CELERY_ENABLED=false`: Disable async processing

**Phase 2 Additional Required:**
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anon/public key
- `SUPABASE_JWT_SECRET`: Supabase JWT secret
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `AUTH_ENABLED=true`: Enable authentication
- `CELERY_ENABLED=true`: Enable async processing
- `CELERY_BROKER_URL`: Redis URL for Celery
- `CELERY_RESULT_BACKEND`: Redis URL for results

**Optional:**
- `QDRANT_HOST`: Qdrant server host (default: localhost)
- `QDRANT_PORT`: Qdrant server port (default: 6333)
- `CHUNK_SIZE`: Document chunk size (default: 1024)
- `CHUNK_OVERLAP`: Chunk overlap (default: 128)
- `TOP_K`: Number of chunks to retrieve (default: 5)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT expiration (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration (default: 7)

## Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:e2e  # End-to-end tests
```

## Deployment

### Production Deployment Options

1. **Cloud VM (AWS, DigitalOcean, etc.)**
   ```bash
   # SSH to server
   git clone repo
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Kubernetes**
   ```bash
   kubectl apply -f k8s/
   ```

3. **Separate Services**
   - Frontend: Deploy to Vercel/Netlify
   - Backend: Deploy to Railway/Render
   - Database: Managed PostgreSQL (AWS RDS, etc.)

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Monitoring

- **Health Endpoint**: `/api/v1/health`
- **Metrics**: Prometheus metrics at `/metrics`
- **Logs**: Structured JSON logging
- **Error Tracking**: Integrate Sentry for production

## Security

- JWT-based authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- SQL injection prevention
- Rate limiting on APIs
- CORS configuration
- HTTPS in production
- Environment variable secrets

## Performance

- **Query Response**: < 3 seconds (P95)
- **Document Processing**: ~2 minutes for 50-page PDF
- **Concurrent Users**: 100+ supported
- **Caching**: Redis for frequent queries
- **Async Processing**: Celery for background tasks

## Troubleshooting

### Common Issues

**"Connection refused" errors:**
- Ensure all Docker containers are running: `docker-compose ps`
- Check logs: `docker-compose logs <service-name>`

**OpenAI API errors:**
- Verify API key is correct in `.env`
- Check API quota and billing

**Document upload fails:**
- Check file size limits
- Verify supported file format
- Check backend logs

**Slow query responses:**
- Check OpenAI API latency
- Verify Redis is running
- Check Qdrant index size

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- OpenAI for GPT-4 and embeddings API
- Qdrant team for the vector database
- LangChain community for RAG framework
- FastAPI and Next.js communities

## Contact

For questions or support, please open an issue on GitHub.

## Roadmap

### Completed ✅
- [x] Multi-tenancy support (Phase 2)
- [x] User authentication and authorization (Phase 2)
- [x] Async processing with job tracking (Phase 2)
- [x] Cloud storage integration (Phase 2)
- [x] Row-level security (Phase 2)

### In Progress 🚧
- [ ] Advanced analytics dashboard
- [ ] Fine-tuned embeddings for finance
- [ ] Multi-modal support (charts, images)

### Planned 📋
- [ ] Mobile application
- [ ] Collaboration features (shared documents)
- [ ] Integration with external data sources (Bloomberg, Reuters)
- [ ] Custom model fine-tuning
- [ ] Document version control
- [ ] Audit logging and compliance features

## Architecture

```
Phase 1 (MVP):                    Phase 2 (Production):
┌──────────┐                      ┌──────────┐
│ Next.js  │                      │ Next.js  │ (Auth Context)
└────┬─────┘                      └────┬─────┘
     │                                 │
     ▼                                 ▼
┌──────────┐                      ┌──────────┐
│ FastAPI  │                      │ FastAPI  │ (Auth Middleware)
└────┬─────┘                      └────┬─────┘
     │                                 │
     ▼                            ┌────┴────┬─────────┬─────────┐
┌──────────┐                      ▼         ▼         ▼         ▼
│  Qdrant  │                   Supabase   Redis    Qdrant    Celery
└──────────┘                   (DB+Auth)  (Queue) (Vectors) (Workers)
```

See [PHASE2_IMPLEMENTATION_PLAN.md](PHASE2_IMPLEMENTATION_PLAN.md) for detailed technical architecture and design decisions.
