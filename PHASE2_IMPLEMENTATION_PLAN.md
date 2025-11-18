# Phase 2 Implementation Plan - Financial RAG System

**Phase:** 2 of 3
**Timeline:** 2-3 weeks
**Status:** In Progress
**Started:** 2025-11-12

---

## Phase 2 Objectives

Transform the Phase 1 MVP into a production-ready multi-user system with:
1. **User Authentication** - Secure login/signup via Supabase Auth
2. **Document Isolation** - Users can only access their own documents
3. **Async Processing** - Background document processing with Celery
4. **Processing Status** - Real-time updates on document processing
5. **Document Metadata** - Rich metadata in PostgreSQL via Supabase
6. **File Storage** - Secure file storage in Supabase Storage

---

## Architecture Changes

### Current (Phase 1)
```
Frontend → FastAPI → Qdrant
                  ↓
            Local File System
```

### Phase 2
```
Frontend → FastAPI → Supabase Auth (JWT)
                  ↓
                  ├→ Supabase DB (PostgreSQL) - Metadata
                  ├→ Supabase Storage - Files
                  ├→ Qdrant - Vectors
                  └→ Redis → Celery Workers
                              ↓
                        Document Processing
                        (Extract, Chunk, Embed)
```

---

## Implementation Roadmap

### Week 1: Database & Authentication

#### Task 1.1: Supabase Setup
- [x] Create Supabase project
- [x] Set up database schema
- [x] Configure Row Level Security (RLS)
- [x] Set up Supabase Storage buckets
- [x] Generate API keys

**Database Schema:**
```sql
-- Users table (managed by Supabase Auth)
-- auth.users (built-in)

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    processing_job_id TEXT,

    -- Processing metadata
    total_pages INTEGER,
    total_chunks INTEGER,
    processing_time_ms INTEGER,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Document chunks table (for reference)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    vector_id TEXT NOT NULL, -- Qdrant point ID
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processing jobs table
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued', -- queued, processing, completed, failed
    task_id TEXT NOT NULL, -- Celery task ID
    progress INTEGER DEFAULT 0, -- 0-100
    current_step TEXT, -- extraction, chunking, embedding, storage
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User settings table
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_processing_jobs_document_id ON processing_jobs(document_id);
CREATE INDEX idx_processing_jobs_user_id ON processing_jobs(user_id);
CREATE INDEX idx_processing_jobs_status ON processing_jobs(status);

-- Row Level Security (RLS)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies for documents
CREATE POLICY "Users can view their own documents"
    ON documents FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents"
    ON documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own documents"
    ON documents FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own documents"
    ON documents FOR DELETE
    USING (auth.uid() = user_id);

-- Similar policies for other tables...
```

#### Task 1.2: Backend Supabase Integration
- [ ] Install Supabase Python client
- [ ] Create Supabase service (`backend/app/services/supabase_service.py`)
- [ ] Add Supabase config to settings
- [ ] Implement JWT authentication middleware
- [ ] Update document routes to use Supabase

#### Task 1.3: Frontend Authentication
- [ ] Install Supabase JS client
- [ ] Create auth context/hooks
- [ ] Build login/signup pages
- [ ] Add protected routes
- [ ] Update API client with JWT tokens

### Week 2: Async Processing

#### Task 2.1: Redis & Celery Setup
- [ ] Set up Redis (Docker)
- [ ] Install Celery and dependencies
- [ ] Configure Celery app
- [ ] Create Celery tasks for document processing
- [ ] Add task monitoring (Flower)

**Celery Tasks:**
```python
# backend/app/tasks/document_tasks.py

@celery_app.task(bind=True)
def process_document_async(self, document_id: str, user_id: str):
    """
    Async document processing task.

    Steps:
    1. Extract text
    2. Chunk text
    3. Generate embeddings
    4. Store in Qdrant
    5. Update database
    """
    try:
        # Update status: processing
        update_job_status(self.request.id, 'processing', 0)

        # Step 1: Extract (25%)
        text = extract_text_from_file(document_id)
        update_job_status(self.request.id, 'processing', 25, 'extraction')

        # Step 2: Chunk (50%)
        chunks = chunk_text(text)
        update_job_status(self.request.id, 'processing', 50, 'chunking')

        # Step 3: Embed (75%)
        embeddings = generate_embeddings(chunks)
        update_job_status(self.request.id, 'processing', 75, 'embedding')

        # Step 4: Store (100%)
        store_in_qdrant(embeddings)
        update_job_status(self.request.id, 'completed', 100, 'completed')

    except Exception as e:
        update_job_status(self.request.id, 'failed', 0, error=str(e))
        raise
```

#### Task 2.2: Processing Status Tracking
- [ ] Create processing jobs API endpoints
- [ ] Implement WebSocket for real-time updates (optional)
- [ ] Add polling mechanism for status updates
- [ ] Update frontend to show processing progress

#### Task 2.3: Update Document Upload Flow
- [ ] Change upload to queue async task
- [ ] Return job ID immediately
- [ ] Remove synchronous processing
- [ ] Add status polling on frontend

### Week 3: Enhanced Features & Polish

#### Task 3.1: User Profile & Settings
- [ ] Create user profile page
- [ ] Add user settings (preferences)
- [ ] Document management per user
- [ ] Usage statistics per user

#### Task 3.2: Document Sharing (Optional)
- [ ] Add sharing permissions table
- [ ] Implement share links
- [ ] Add collaborator management
- [ ] Update RLS policies

#### Task 3.3: Testing & Documentation
- [ ] Add unit tests for new features
- [ ] Add integration tests
- [ ] Update API documentation
- [ ] Update README with new setup instructions

---

## Technical Specifications

### Backend Dependencies

Add to `backend/requirements.txt`:
```
# Supabase
supabase>=2.0.0
gotrue>=2.0.0

# Celery & Redis
celery>=5.3.0
redis>=5.0.0
flower>=2.0.0  # Celery monitoring

# Additional
python-jose>=3.3.0  # JWT handling
passlib>=1.7.4  # Password hashing (if needed)
```

### Frontend Dependencies

Add to `frontend/package.json`:
```json
{
  "dependencies": {
    "@supabase/supabase-js": "^2.38.0",
    "@supabase/auth-helpers-nextjs": "^0.8.0",
    "@supabase/auth-ui-react": "^0.4.0",
    "@supabase/auth-ui-shared": "^0.1.0"
  }
}
```

### Environment Variables

**Backend `.env`:**
```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Redis & Celery
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Feature Flags
ASYNC_PROCESSING_ENABLED=true
AUTH_REQUIRED=true
```

**Frontend `.env.local`:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## New File Structure

### Backend Additions
```
backend/
├── app/
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py              # JWT authentication middleware
│   ├── services/
│   │   ├── supabase_service.py  # Supabase client & operations
│   │   └── user_service.py      # User management
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery configuration
│   │   └── document_tasks.py    # Async document processing
│   ├── api/routes/
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── users.py             # User management endpoints
│   │   └── jobs.py              # Processing job endpoints
│   └── models/
│       ├── __init__.py
│       ├── user.py              # User models
│       ├── document.py          # Document models
│       └── job.py               # Job models
├── celeryconfig.py              # Celery configuration
└── docker-compose.yml           # Redis + Celery services
```

### Frontend Additions
```
frontend/
├── src/
│   ├── contexts/
│   │   └── AuthContext.tsx      # Authentication context
│   ├── hooks/
│   │   ├── useAuth.ts           # Auth hook
│   │   └── useProcessingStatus.ts  # Status polling hook
│   ├── lib/
│   │   └── supabase.ts          # Supabase client
│   ├── app/
│   │   ├── login/
│   │   │   └── page.tsx         # Login page
│   │   ├── signup/
│   │   │   └── page.tsx         # Signup page
│   │   ├── profile/
│   │   │   └── page.tsx         # User profile
│   │   └── middleware.ts        # Auth middleware (Next.js)
│   └── components/
│       ├── AuthGuard.tsx        # Protected route wrapper
│       └── ProcessingStatus.tsx  # Processing progress component
```

---

## API Changes

### New Endpoints

**Authentication:**
```
POST   /api/v1/auth/signup          # Register new user
POST   /api/v1/auth/login           # Login
POST   /api/v1/auth/logout          # Logout
POST   /api/v1/auth/refresh         # Refresh token
GET    /api/v1/auth/me              # Get current user
```

**Users:**
```
GET    /api/v1/users/me             # Get user profile
PUT    /api/v1/users/me             # Update user profile
GET    /api/v1/users/me/stats       # Get user statistics
```

**Processing Jobs:**
```
GET    /api/v1/jobs                 # List user's jobs
GET    /api/v1/jobs/{job_id}        # Get job status
DELETE /api/v1/jobs/{job_id}        # Cancel job
GET    /api/v1/jobs/{job_id}/logs   # Get job logs
```

**Modified Endpoints:**
```
POST   /api/v1/documents/upload     # Now queues async task
GET    /api/v1/documents            # Now filtered by user
DELETE /api/v1/documents/{id}       # Now checks ownership
POST   /api/v1/query                # Now user-scoped
```

---

## Migration Strategy

### Phase 1 → Phase 2 Transition

1. **Database Migration**
   - Export existing documents metadata
   - Import into Supabase
   - Assign to admin user
   - Migrate files to Supabase Storage

2. **Backward Compatibility**
   - Keep Phase 1 endpoints working
   - Add feature flag: `AUTH_REQUIRED=false`
   - Gradual rollout

3. **Testing Strategy**
   - Test with auth disabled (Phase 1 mode)
   - Test with auth enabled (Phase 2 mode)
   - Test migration scripts

---

## Success Criteria

Phase 2 is complete when:
- [x] Users can sign up and log in
- [x] Each user has isolated documents
- [x] Document processing is async
- [x] Users can track processing status
- [x] All documents stored in Supabase
- [x] All tests passing
- [x] Documentation updated
- [x] No breaking changes to Phase 1 functionality

---

## Risk Assessment

### High Risk
- **Database Migration** - Could lose data if not careful
  - Mitigation: Backup everything, test migration thoroughly

- **Auth Breaking Existing Clients** - Phase 1 users can't access
  - Mitigation: Feature flag for auth, backward compatibility mode

### Medium Risk
- **Celery Configuration** - Async processing issues
  - Mitigation: Thorough testing, fallback to sync processing

- **Performance Degradation** - Database queries slower than file system
  - Mitigation: Proper indexing, connection pooling

### Low Risk
- **Supabase Costs** - Free tier might not be enough
  - Mitigation: Monitor usage, optimize queries

---

## Timeline

**Week 1: Nov 12-18**
- Supabase setup
- Database schema
- Authentication backend
- Authentication frontend

**Week 2: Nov 19-25**
- Redis & Celery setup
- Async document processing
- Status tracking
- Frontend updates

**Week 3: Nov 26-Dec 2**
- User profiles
- Document sharing (if time)
- Testing
- Documentation
- Deployment prep

**Total: 3 weeks** (can be compressed to 2 if needed)

---

## Next Steps

1. Create Supabase project
2. Set up database schema
3. Install backend dependencies
4. Implement authentication middleware
5. Update document routes
6. Build login/signup UI
7. Test authentication flow
8. Move to async processing

---

**Document Status:** Planning Complete
**Ready to Start:** Yes
**First Task:** Supabase setup and database schema
