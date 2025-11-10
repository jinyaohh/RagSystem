# Financial Reports RAG System

A production-grade Retrieval-Augmented Generation (RAG) system for querying financial reports using natural language. Built with FastAPI, Next.js, and Qdrant vector database.

## Features

- **Intelligent Document Processing**: Upload and process financial reports (PDF, DOCX, Excel)
- **Natural Language Queries**: Ask questions about your financial documents in plain English
- **Semantic Search**: Advanced vector search with hybrid retrieval for accurate results
- **Real-time Streaming**: Get answers streamed in real-time as they're generated
- **Document Management**: Track, organize, and manage uploaded documents
- **User Authentication**: Secure login and user management
- **Analytics Dashboard**: Track usage, popular queries, and system metrics
- **Citation Support**: Responses include references to source documents

## Tech Stack

### Backend
- **FastAPI**: Modern, fast Python web framework
- **LangChain**: RAG orchestration and prompt management
- **Qdrant**: Vector database for semantic search
- **PostgreSQL**: Relational database for metadata
- **Redis**: Caching and task queue
- **Celery**: Asynchronous task processing
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

- **Docker & Docker Compose**: For containerized development
- **Node.js 18+**: For frontend development
- **Python 3.11+**: For backend development
- **OpenAI API Key**: For embeddings and LLM
- **Git**: Version control

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/RagSystem.git
cd RagSystem
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: OPENAI_API_KEY, DATABASE_URL, REDIS_URL
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

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
- `POST /api/v1/documents/upload` - Upload a document
- `POST /api/v1/query` - Ask a question
- `GET /api/v1/documents` - List all documents
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/health` - Health check

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key

**Optional:**
- `QDRANT_HOST`: Qdrant server host (default: localhost)
- `QDRANT_PORT`: Qdrant server port (default: 6333)
- `CHUNK_SIZE`: Document chunk size (default: 1024)
- `CHUNK_OVERLAP`: Chunk overlap (default: 128)
- `TOP_K`: Number of chunks to retrieve (default: 5)

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

- [ ] Multi-modal support (charts, images)
- [ ] Fine-tuned embeddings for finance
- [ ] Multi-tenancy support
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Collaboration features
- [ ] Integration with external data sources
- [ ] Custom model fine-tuning

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical architecture and design decisions.
