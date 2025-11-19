# Quick Start Guide

Get up and running with the Financial RAG System in minutes.

## Prerequisites

- **Docker** and **Docker Compose** (required)
- **OpenAI API Key** ([get one here](https://platform.openai.com/api-keys))
- **Node.js 18+** and **Python 3.11+** (for development)
- **Git** (for cloning the repository)

## Choose Your Setup

### Option 1: Quick Demo (Phase 1 - MVP)
**Best for:** Testing the system quickly without authentication
**Time:** 10 minutes

### Option 2: Production Setup (Phase 2 + 3)
**Best for:** Multi-user deployment with analytics
**Time:** 30 minutes
**Additional requirements:** Supabase account

---

## Option 1: Quick Demo (Phase 1 - MVP)

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/RagSystem.git
cd RagSystem
```

**Backend setup:**
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your settings:
```bash
OPENAI_API_KEY=your-api-key-here
AUTH_ENABLED=false
CELERY_ENABLED=false
```

**Frontend setup:**
```bash
cd frontend
cp .env.example .env.local
```

Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Note:** Configuration files are in `backend/.env` and `frontend/.env.local`, not in the root directory.

### 2. Start Services

```bash
# Start Qdrant vector database
cd backend
docker-compose up -d qdrant

# Install backend dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend
uvicorn app.main:app --reload --port 8000
```

In a new terminal:
```bash
# Install and start frontend
cd frontend
npm install
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### 4. Try It Out

1. Upload a document (PDF, DOCX, or XLSX)
2. Wait for processing to complete
3. Go to Chat and ask questions about your document

**Example questions:**
- "What is the main topic of this document?"
- "Summarize the key findings"
- "What are the revenue figures mentioned?"

---

## Option 2: Production Setup (Phase 2 + 3)

Full multi-user system with authentication, async processing, and analytics.

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Copy your project credentials:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon/Public Key
   - Service Role Key
   - JWT Secret (Project Settings → API → JWT Settings)

### 2. Set Up Database Schema

Copy the contents of `backend/supabase_schema.sql` and run in Supabase SQL Editor:

```bash
cat backend/supabase_schema.sql
```

Then copy and paste into Supabase SQL Editor and execute.

Repeat for analytics schema:
```bash
cat backend/supabase_analytics_schema.sql
```

### 3. Configure Environment

Backend `.env`:
```bash
# OpenAI
OPENAI_API_KEY=your-openai-key

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Enable Features
AUTH_ENABLED=true
CELERY_ENABLED=true

# Redis & Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

Frontend `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Start All Services

```bash
# Start all backend services (Qdrant, Redis, Celery)
cd backend
docker-compose up -d

# Start backend API
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal:
```bash
# Start Celery worker
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

In another terminal:
```bash
# Start frontend
cd frontend
npm install
npm run dev
```

### 5. Create Your Account

1. Go to http://localhost:3000
2. Click "Sign Up"
3. Create your account with email and password
4. Log in

### 6. Explore Features

**Documents:**
- Upload documents (async processing in background)
- Track processing progress in Jobs page
- Manage your document library

**Chat:**
- Ask questions about your documents
- Get AI-powered answers with source citations
- View answer confidence and sources

**Jobs:**
- Monitor document processing status
- View processing progress (extraction → chunking → embedding → storage)
- Cancel jobs if needed

**Analytics:**
- View your usage statistics
- Track query patterns and popular questions
- Monitor document usage and performance metrics
- See activity trends over time

---

## Common Commands

### Check Service Health

```bash
# Backend health check
curl http://localhost:8000/api/v1/health

# Detailed health check
curl http://localhost:8000/api/v1/health/detailed

# Analytics health (if enabled)
curl http://localhost:8000/api/v1/analytics/health
```

### View Logs

```bash
# Backend logs
tail -f logs/app.log

# Celery worker logs
docker-compose logs -f celery

# Redis logs
docker-compose logs -f redis
```

### Stop Services

```bash
# Stop Docker services
docker-compose down

# Stop backend/frontend: Ctrl+C in respective terminals
```

---

## Troubleshooting

### "Connection refused" errors
- Ensure Docker containers are running: `docker-compose ps`
- Check if ports are available: `lsof -i :8000,3000,6333,6379`

### OpenAI API errors
- Verify API key is correct in `.env`
- Check API quota: https://platform.openai.com/usage

### Document upload fails
- Check file size (< 50MB recommended)
- Verify file format (PDF, DOCX, XLSX, TXT)
- Check backend logs for details

### "Analytics require authentication" error
- Set `AUTH_ENABLED=true` in backend `.env`
- Analytics only available with authentication enabled

### Slow query responses
- First query may take longer (model initialization)
- Check OpenAI API status
- Verify Redis is running: `docker-compose ps redis`

---

## Next Steps

### Phase 1 Users:
- Read [docs/setup/PHASE2_PRODUCTION.md](docs/setup/PHASE2_PRODUCTION.md) to upgrade to multi-user
- Explore the [API documentation](http://localhost:8000/docs)

### Phase 2 Users:
- Read [docs/setup/PHASE3_ANALYTICS.md](docs/setup/PHASE3_ANALYTICS.md) to add analytics
- Review [USER_MANUAL.md](USER_MANUAL.md) for detailed feature guide

### Developers:
- Read [CLAUDE.md](CLAUDE.md) for development and maintenance guide
- Check [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for system design
- See [docs/guides/QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md) for API examples

---

## Getting Help

- **Documentation**: Browse the [docs/](docs/) folder
- **API Reference**: http://localhost:8000/docs (when running)
- **Issues**: Check existing issues or create a new one on GitHub

## Quick Links

- [Full README](README.md) - Complete project overview
- [User Manual](USER_MANUAL.md) - Comprehensive user guide
- [Phase 2 Setup](docs/setup/PHASE2_PRODUCTION.md) - Production deployment
- [Phase 3 Setup](docs/setup/PHASE3_ANALYTICS.md) - Analytics dashboard
- [Architecture](docs/architecture/ARCHITECTURE.md) - Technical design
- [Developer Guide](CLAUDE.md) - For contributors and maintainers
