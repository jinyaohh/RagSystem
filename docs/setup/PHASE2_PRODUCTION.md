# Phase 2 Setup Guide

This guide explains how to set up and use the Phase 2 features of the Financial RAG System, including authentication, async processing, and job tracking.

## Overview

Phase 2 transforms the MVP (Phase 1) into a production-ready multi-user system with:

- **User Authentication**: JWT-based authentication using Supabase Auth
- **Async Processing**: Background document processing with Celery and Redis
- **Job Tracking**: Real-time monitoring of document processing jobs
- **User Isolation**: Row-level security ensuring users only see their own data
- **Scalability**: Distributed task processing for handling multiple uploads

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Supabase account (free tier is sufficient)
- Redis (provided via Docker)

## Phase 2 vs Phase 1

| Feature | Phase 1 (MVP) | Phase 2 (Production) |
|---------|---------------|----------------------|
| Authentication | No | Yes (JWT + Supabase) |
| Processing | Synchronous | Asynchronous (Celery) |
| User Management | Single user | Multi-user with isolation |
| Job Tracking | No | Yes (real-time status) |
| Storage | Local filesystem | Supabase Storage |
| Database | File-based | PostgreSQL (Supabase) |
| Scalability | Limited | Horizontally scalable |

## Architecture

```
┌─────────────────┐
│  Next.js UI     │  Frontend with auth context
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │  Routes with auth middleware
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────┐
    ▼         ▼          ▼         ▼
┌────────┐ ┌────┐  ┌─────────┐ ┌────────┐
│Supabase│ │Redis│  │ Qdrant  │ │ Celery │
│  DB    │ │Queue│  │ Vectors │ │Workers │
└────────┘ └────┘  └─────────┘ └────────┘
```

## Backend Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note down your:
   - Project URL (e.g., `https://xxxxx.supabase.co`)
   - Anon/Public Key
   - Service Role Key
   - JWT Secret (found in Project Settings → API → JWT Settings)

### 2. Set Up Database Schema

Execute the SQL schema in Supabase SQL Editor:

```bash
# Copy the schema file content
cat backend/supabase_schema.sql
```

Then paste and run it in Supabase SQL Editor (or use Supabase CLI):

```bash
# Using Supabase CLI
supabase db push
```

This creates:
- `documents` table with user relationships
- `processing_jobs` table for job tracking
- `document_chunks` table for vector metadata
- `user_settings` and `user_stats` tables
- Row Level Security (RLS) policies
- Automatic triggers and functions

### 3. Configure Environment Variables

Update `backend/.env`:

```bash
# Phase 2: Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Phase 2: Authentication
AUTH_ENABLED=true
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Phase 2: Async Processing
CELERY_ENABLED=true
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_ENABLED=true

# Supabase Storage
SUPABASE_STORAGE_BUCKET=documents
```

### 4. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New Phase 2 dependencies include:
- `supabase` - Supabase Python client
- `python-jose[cryptography]` - JWT handling
- `passlib[bcrypt]` - Password hashing
- `celery` - Distributed task queue
- `redis` - Message broker
- `flower` - Celery monitoring UI

### 5. Start Services with Docker Compose

```bash
cd backend
docker-compose up -d
```

This starts:
- **Redis** (port 6379) - Message broker for Celery
- **Qdrant** (port 6333, 6334) - Vector database
- **Celery Worker** - Background task processor
- **Flower** (port 5555) - Celery monitoring dashboard

Verify services are running:

```bash
docker-compose ps
```

### 6. Start FastAPI Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Verify Phase 2 features are enabled:

```bash
curl http://localhost:8000/health/detailed
```

Should show:
```json
{
  "status": "healthy",
  "feature_flags": {
    "auth_enabled": true,
    "celery_enabled": true
  },
  "services": {
    "supabase": { "status": "connected" },
    "celery": { "status": "healthy", "workers": 1 }
  }
}
```

## Frontend Setup

### 1. Configure Environment Variables

Update `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Financial RAG System
```

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

Frontend will be available at http://localhost:3000

## Using Phase 2 Features

### User Authentication

#### Sign Up

1. Navigate to http://localhost:3000/signup
2. Enter email, password, and optional full name
3. Click "Sign Up"
4. You'll be automatically logged in and redirected to the upload page

#### Login

1. Navigate to http://localhost:3000/login
2. Enter email and password
3. Click "Sign In"
4. Redirected to upload page upon success

#### Logout

Click the "Logout" button in the header (visible when authenticated)

### Document Upload with Async Processing

#### Upload a Document

1. Log in to your account
2. Navigate to Upload page
3. Drag and drop a document or click "Browse Files"
4. Click "Upload and Process"
5. You'll see a success message with a Job ID
6. Click "View Jobs" to monitor processing

#### Monitor Job Progress

1. Navigate to Jobs page (http://localhost:3000/jobs)
2. View all your processing jobs
3. Jobs auto-refresh every 3 seconds
4. See real-time progress (0-100%)
5. View current processing step:
   - Queued
   - Extracting text
   - Chunking document
   - Generating embeddings
   - Storing vectors
   - Completed

#### Cancel a Job

1. On the Jobs page, find a processing or queued job
2. Click "Cancel" button
3. Job will be terminated and marked as cancelled

### View Documents

1. Navigate to Documents page
2. See only your uploaded documents (user-scoped)
3. View processing status and metadata

### Query Documents

1. Navigate to Chat page
2. Ask questions about your documents
3. Queries are user-scoped (only search your documents)

## Monitoring and Debugging

### Celery Worker Logs

```bash
docker-compose logs -f celery_worker
```

### Flower Dashboard

Open http://localhost:5555 to see:
- Active workers
- Running tasks
- Task history
- Success/failure rates

### Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to:
   - **Table Editor**: View database records
   - **Authentication**: Manage users
   - **Storage**: View uploaded files
   - **Database → Replication**: Monitor RLS policies

### API Endpoints

#### Authentication Endpoints

- `POST /api/v1/auth/signup` - Create new account
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

#### Job Tracking Endpoints

- `GET /api/v1/jobs/` - List all jobs (user-scoped)
- `GET /api/v1/jobs/{job_id}` - Get job details
- `POST /api/v1/jobs/{job_id}/cancel` - Cancel a job

#### Document Endpoints (Enhanced)

- `POST /api/v1/documents/upload-and-process` - Upload and queue processing
  - Without auth: Synchronous processing (Phase 1)
  - With auth: Async processing with job ID (Phase 2)

## Feature Flags

Phase 2 uses feature flags for gradual rollout:

```python
# backend/app/core/config.py
AUTH_ENABLED = true   # Enable authentication
CELERY_ENABLED = true # Enable async processing
```

### Phase 1 Mode (Backward Compatible)

Set in `.env`:
```bash
AUTH_ENABLED=false
CELERY_ENABLED=false
```

System runs in Phase 1 mode:
- No authentication required
- Synchronous document processing
- File-based storage
- Single-user experience

### Phase 2 Mode (Production)

Set in `.env`:
```bash
AUTH_ENABLED=true
CELERY_ENABLED=true
```

System runs in Phase 2 mode:
- Authentication required for protected routes
- Async document processing
- Supabase storage
- Multi-user with isolation

## Security

### Row Level Security (RLS)

All tables have RLS policies ensuring:
- Users can only view/edit their own documents
- Users can only view/cancel their own jobs
- Automatic user_id filtering in queries

### JWT Authentication

- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
- Tokens stored in localStorage (frontend)
- Bearer token authentication in headers

### Password Security

- Passwords hashed with bcrypt via Supabase Auth
- Minimum 6 characters required
- Never stored in plain text

## Scaling

### Horizontal Scaling

#### Add More Celery Workers

```bash
# Scale to 3 workers
docker-compose up -d --scale celery_worker=3
```

#### Deploy Multiple Backend Instances

Use a load balancer (nginx, AWS ALB) to distribute traffic:

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Vertical Scaling

Increase resources for:
- Celery workers (CPU for embeddings)
- Redis (memory for queue)
- Supabase (database connections)

## Troubleshooting

### "Authentication Required" Error

**Cause**: AUTH_ENABLED=true but user not logged in

**Solution**:
1. Log in at http://localhost:3000/login
2. Or disable auth: `AUTH_ENABLED=false` in `.env`

### Jobs Stuck in "Queued" Status

**Cause**: Celery worker not running

**Solution**:
```bash
docker-compose ps celery_worker
docker-compose logs celery_worker
docker-compose restart celery_worker
```

### "Supabase Connection Error"

**Cause**: Invalid credentials or network issue

**Solution**:
1. Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
2. Check Supabase project status
3. Test connection:
   ```bash
   curl https://your-project.supabase.co/rest/v1/
   ```

### RLS Policy Blocking Queries

**Cause**: RLS policy preventing access

**Solution**:
1. Check SQL schema was executed correctly
2. Verify `user_id` matches authenticated user
3. Use Supabase dashboard to test policies

### Document Upload Fails with "401 Unauthorized"

**Cause**: Missing or expired JWT token

**Solution**:
1. Log out and log back in
2. Check browser console for token errors
3. Verify `JWT_SECRET` matches between Supabase and backend

## Production Deployment

### Environment Variables

Set production values for:

```bash
# Supabase (production project)
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_KEY=prod-anon-key
SUPABASE_JWT_SECRET=prod-jwt-secret

# Security
SECRET_KEY=generate-strong-random-key
ALLOWED_ORIGINS=https://yourdomain.com

# Redis (managed service recommended)
CELERY_BROKER_URL=redis://prod-redis:6379/0

# Qdrant (managed or self-hosted)
QDRANT_HOST=prod-qdrant.example.com
```

### Deployment Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Use managed Redis (AWS ElastiCache, Redis Cloud)
- [ ] Use managed PostgreSQL (Supabase production tier)
- [ ] Enable HTTPS for all services
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure log aggregation
- [ ] Set up automated backups (Supabase handles this)
- [ ] Enable rate limiting on API
- [ ] Configure Celery auto-scaling

## Next Steps

1. **Test the system**: Create an account and upload documents
2. **Monitor jobs**: Watch real-time progress in the Jobs page
3. **Check Flower**: View Celery tasks at http://localhost:5555
4. **Explore Supabase**: View data in Supabase dashboard
5. **Scale workers**: Add more Celery workers for throughput
6. **Customize**: Adjust processing steps, chunk sizes, etc.

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review Supabase dashboard for database issues
3. Check Flower dashboard for Celery issues
4. Consult PHASE2_IMPLEMENTATION_PLAN.md for architecture details

## Phase 2 Complete!

You now have a production-ready multi-user RAG system with:
- ✅ User authentication and management
- ✅ Async document processing
- ✅ Real-time job tracking
- ✅ User data isolation
- ✅ Scalable architecture
- ✅ Monitoring and debugging tools
