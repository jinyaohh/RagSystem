# Quick Start Guide

Get your Financial RAG System up and running in minutes!

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Docker Desktop installed and running
- [ ] Git installed
- [ ] OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- [ ] Text editor (VS Code recommended)
- [ ] 8GB+ RAM available
- [ ] 10GB+ disk space

## 5-Minute Setup

### Step 1: Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd RagSystem

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Minimum required: OPENAI_API_KEY=sk-...
nano .env  # or use your preferred editor
```

### Step 2: Start Everything with Docker

```bash
# Start all services (first time takes 5-10 minutes)
docker-compose up -d

# Watch the logs to see progress
docker-compose logs -f
```

### Step 3: Verify Everything is Running

```bash
# Check service status (all should show "running")
docker-compose ps

# Expected output:
# NAME                STATUS              PORTS
# rag-backend         Up                  0.0.0.0:8000->8000/tcp
# rag-frontend        Up                  0.0.0.0:3000->3000/tcp
# rag-postgres        Up                  0.0.0.0:5432->5432/tcp
# rag-redis           Up                  0.0.0.0:6379->6379/tcp
# rag-qdrant          Up                  0.0.0.0:6333->6333/tcp
```

### Step 4: Access the Application

Open your browser and visit:

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### Step 5: Test the System

1. Open http://localhost:3000
2. Sign up for an account (use any email/password for local development)
3. Upload a sample PDF document
4. Wait for processing to complete (~1-2 minutes)
5. Ask a question about the document in the chat interface

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Restart a specific service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build

# Stop and remove all data
docker-compose down -v
```

## Development Workflow

### Backend Development

```bash
# Enter backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run backend locally (not in Docker)
uvicorn app.main:app --reload
```

### Frontend Development

```bash
# Enter frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

## Troubleshooting

### Problem: "Port already in use"

```bash
# Find and kill process using port 8000 (or other port)
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```

### Problem: "Cannot connect to Docker daemon"

```bash
# Make sure Docker Desktop is running
# On Linux, start Docker service:
sudo systemctl start docker
```

### Problem: Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Missing OPENAI_API_KEY in .env
# 2. Database not ready (wait 30 seconds and check again)
# 3. Port 8000 already in use

# Reset and rebuild
docker-compose down -v
docker-compose up -d --build
```

### Problem: Frontend shows "Cannot connect to backend"

```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check NEXT_PUBLIC_API_URL in .env
# Should be: http://localhost:8000

# Restart frontend
docker-compose restart frontend
```

### Problem: Document upload fails

```bash
# Check upload directory permissions
ls -la data/uploads

# Check Celery worker is running
docker-compose ps celery-worker

# View Celery logs
docker-compose logs celery-worker

# Common issues:
# 1. File too large (check MAX_FILE_SIZE in .env)
# 2. OpenAI API key invalid
# 3. Qdrant not ready
```

### Problem: Slow query responses

```bash
# Check OpenAI API status
curl https://status.openai.com/

# Check Redis is running
docker-compose ps redis

# Enable debug logging
# In .env, set: LOG_LEVEL=DEBUG
docker-compose restart backend
```

## Health Checks

```bash
# Backend health
curl http://localhost:8000/api/v1/health

# Qdrant health
curl http://localhost:6333/health

# Redis health
docker-compose exec redis redis-cli ping

# PostgreSQL health
docker-compose exec postgres pg_isready
```

## Monitoring

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Resource Usage

```bash
# Docker stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## Sample Test Data

For testing, you can use these sample financial documents:

1. **Sample Annual Report**: Create a simple PDF with financial data
2. **Sample 10-K Filing**: Download from SEC Edgar
3. **Sample Earnings Report**: Create a test document

Example questions to ask:
- "What was the total revenue?"
- "What are the main risk factors?"
- "Summarize the financial highlights"
- "What is the net income for the year?"

## Next Steps

1. **Read the Documentation**
   - [Architecture Overview](../ARCHITECTURE.md)
   - [Tech Stack Comparison](./TECH_STACK_COMPARISON.md)
   - [API Documentation](http://localhost:8000/docs)

2. **Customize the System**
   - Modify prompts in `backend/app/services/rag_service.py`
   - Adjust chunk size in `.env`
   - Change UI theme in `frontend/src/styles/`

3. **Add Features**
   - Implement user authentication
   - Add document filters
   - Create analytics dashboard
   - Add export functionality

4. **Deploy to Production**
   - See [Deployment Guide](./DEPLOYMENT.md)
   - Set up monitoring
   - Configure backups
   - Set up CI/CD

## Getting Help

- **Check Logs**: Most issues show up in logs
- **API Docs**: http://localhost:8000/docs for API reference
- **GitHub Issues**: Open an issue for bugs
- **Documentation**: Read the full docs in `/docs`

## Production Deployment

Once you're ready to deploy:

```bash
# 1. Set environment to production
ENVIRONMENT=production

# 2. Disable debug mode
DEBUG=False

# 3. Set strong secret keys
SECRET_KEY=<generate-strong-key>

# 4. Use production database
DATABASE_URL=<production-postgres-url>

# 5. Configure domain and SSL
# See DEPLOYMENT.md for details

# 6. Build and deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Success Criteria

You'll know everything is working when:

- ✅ All services show "Up" in `docker-compose ps`
- ✅ Frontend loads at http://localhost:3000
- ✅ You can create an account
- ✅ You can upload a document
- ✅ Document processing completes
- ✅ You can ask questions and get answers
- ✅ Answers include relevant citations

Congratulations! Your Financial RAG System is running! 🎉

## What's Next?

Now that your system is running, you can:

1. Upload your own financial documents
2. Experiment with different types of questions
3. Customize the prompts for better responses
4. Add new features
5. Deploy to production
6. Add to your portfolio/resume

Happy building! 🚀
