# Quick Reference - Phase 1 Implementation

## 📋 Overview

**Goal**: Build a working RAG prototype in 2 weeks
**Approach**: Iterative - start simple, get it working, then enhance

---

## 🎯 Phase 1 Goals (Weeks 1-2)

### Week 1: Backend
- ✅ FastAPI server running
- ✅ Can upload PDFs
- ✅ PDF → text → chunks → embeddings → Qdrant
- ✅ Query endpoint returns RAG answers

### Week 2: Frontend
- ✅ Next.js app running
- ✅ Upload page functional
- ✅ Chat interface working
- ✅ End-to-end RAG flow

---

## 🛠️ Tech Stack (Phase 1 - Minimal)

```
Backend:
  ├─ FastAPI (Python web framework)
  ├─ LangChain (RAG orchestration)
  ├─ OpenAI (GPT-4 + embeddings)
  ├─ Qdrant (vector database)
  └─ pdfplumber (PDF parsing)

Frontend:
  ├─ Next.js 14 (React framework)
  ├─ TypeScript
  ├─ Tailwind CSS
  └─ shadcn/ui (UI components)
```

**Not in Phase 1:**
- ❌ Supabase (add in Phase 2)
- ❌ Authentication (add in Phase 2)
- ❌ Celery (add in Phase 2)
- ❌ Redis (add in Phase 3)

---

## 🚀 Quick Start Commands

### Backend Setup
```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# Run backend
uvicorn app.main:app --reload

# Backend runs at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### Frontend Setup
```bash
# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --app

# Install shadcn/ui
cd frontend
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card

# Run frontend
npm run dev

# Frontend runs at: http://localhost:3000
```

---

## 📁 Project Structure (Phase 1)

```
RagSystem/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app
│   │   ├── core/
│   │   │   └── config.py              # Settings
│   │   ├── api/routes/
│   │   │   ├── documents.py           # Upload endpoint
│   │   │   └── query.py               # Query endpoint
│   │   └── services/
│   │       ├── document_service.py    # PDF processing
│   │       ├── chunking_service.py    # Text chunking
│   │       ├── embedding_service.py   # OpenAI embeddings
│   │       ├── vector_service.py      # Qdrant storage
│   │       ├── retrieval_service.py   # Vector search
│   │       ├── prompt_service.py      # Prompt templates
│   │       ├── llm_service.py         # GPT-4 calls
│   │       └── rag_service.py         # RAG orchestration
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                 # Main layout
│   │   ├── page.tsx                   # Home page
│   │   ├── upload/page.tsx            # Upload page
│   │   └── chat/page.tsx              # Chat page
│   ├── lib/
│   │   └── api.ts                     # API client
│   ├── components/
│   │   └── ui/                        # shadcn components
│   └── package.json
│
└── docs/
    ├── IMPLEMENTATION_PLAN.md         # Full plan
    ├── PHASE_1_TASKS.md              # Detailed tasks
    └── QUICK_REFERENCE.md            # This file
```

---

## 🔑 Environment Variables

### Backend (.env)
```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# RAG Settings
CHUNK_SIZE=1024
CHUNK_OVERLAP=128
TOP_K=5

# Optional
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📝 Key Files to Create

### Week 1 (Backend)

**Day 1-2: Setup**
1. `backend/requirements.txt` - Dependencies
2. `backend/app/main.py` - FastAPI app
3. `backend/app/core/config.py` - Configuration
4. `backend/.env` - Environment variables

**Day 3-4: Document Processing**
5. `backend/app/api/routes/documents.py` - Upload endpoint
6. `backend/app/services/document_service.py` - PDF extraction
7. `backend/app/services/chunking_service.py` - Text chunking
8. `backend/app/services/embedding_service.py` - Embeddings
9. `backend/app/services/vector_service.py` - Qdrant storage

**Day 5-7: RAG Pipeline**
10. `backend/app/services/retrieval_service.py` - Vector search
11. `backend/app/services/prompt_service.py` - Prompts
12. `backend/app/services/llm_service.py` - GPT-4
13. `backend/app/services/rag_service.py` - Orchestration
14. `backend/app/api/routes/query.py` - Query endpoint

### Week 2 (Frontend)

**Day 8-9: Setup**
1. `frontend/lib/api.ts` - API client
2. `frontend/app/layout.tsx` - Layout
3. `frontend/components/nav.tsx` - Navigation

**Day 10-11: Upload UI**
4. `frontend/app/upload/page.tsx` - Upload page
5. `frontend/components/upload-form.tsx` - Upload form

**Day 12-14: Chat UI**
6. `frontend/app/chat/page.tsx` - Chat page
7. `frontend/components/message.tsx` - Message component
8. `frontend/components/chat-input.tsx` - Input component

---

## 🧪 Testing Strategy

### Manual Testing

**Backend:**
```bash
# 1. Test health check
curl http://localhost:8000/health

# 2. Test document upload
curl -X POST http://localhost:8000/documents/upload-and-process \
  -F "file=@sample.pdf"

# 3. Test query
curl -X POST http://localhost:8000/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the revenue?"}'
```

**Frontend:**
1. Open http://localhost:3000
2. Navigate to /upload
3. Upload a PDF
4. Wait for processing
5. Navigate to /chat
6. Ask a question
7. Verify answer appears with citations

### Automated Testing (Later)
- Unit tests for services
- Integration tests for endpoints
- E2E tests for user flows

---

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError"
**Solution:** Make sure virtual environment is activated
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: "Qdrant connection refused"
**Solution:** Make sure Qdrant is running
```bash
docker ps  # Check if Qdrant container is running
docker run -p 6333:6333 qdrant/qdrant  # Start Qdrant
```

### Issue: "OpenAI API error"
**Solution:** Check API key and credits
```bash
# Verify key is in .env
cat backend/.env | grep OPENAI_API_KEY

# Test key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: "CORS error in frontend"
**Solution:** Make sure CORS is configured in FastAPI
```python
# In backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Frontend can't connect to backend"
**Solution:** Check environment variable
```bash
# In frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📊 Progress Tracking

### Week 1 Checklist
- [ ] Day 1-2: Backend setup complete
  - [ ] Virtual environment created
  - [ ] Dependencies installed
  - [ ] FastAPI running
  - [ ] Qdrant connected
  - [ ] OpenAI tested

- [ ] Day 3-4: Document processing complete
  - [ ] Upload endpoint works
  - [ ] PDF text extraction works
  - [ ] Text chunking works
  - [ ] Embeddings generated
  - [ ] Vectors stored in Qdrant

- [ ] Day 5-7: RAG pipeline complete
  - [ ] Query endpoint works
  - [ ] Vector search works
  - [ ] Prompt formatting works
  - [ ] GPT-4 returns answers
  - [ ] Complete RAG flow tested

### Week 2 Checklist
- [ ] Day 8-9: Frontend setup complete
  - [ ] Next.js app created
  - [ ] shadcn/ui installed
  - [ ] API client working
  - [ ] Can call backend

- [ ] Day 10-11: Upload UI complete
  - [ ] Upload page created
  - [ ] File selection works
  - [ ] Upload triggers processing
  - [ ] Shows processing status
  - [ ] Displays results

- [ ] Day 12-14: Chat UI complete
  - [ ] Chat page created
  - [ ] Can send messages
  - [ ] Messages display correctly
  - [ ] Shows loading state
  - [ ] Citations displayed
  - [ ] End-to-end flow works

---

## ✅ Phase 1 Success Criteria

You've successfully completed Phase 1 when:

1. **Backend Works:**
   - ✅ FastAPI server running
   - ✅ Can upload PDF via API
   - ✅ PDF is processed and embedded
   - ✅ Can query via API
   - ✅ Returns answer with citations

2. **Frontend Works:**
   - ✅ Next.js app running
   - ✅ Upload page functional
   - ✅ Chat page functional
   - ✅ Can upload PDFs via UI
   - ✅ Can ask questions via UI

3. **Integration Works:**
   - ✅ Frontend → Backend communication
   - ✅ Upload PDF → Process → Query → Answer
   - ✅ Complete RAG pipeline working
   - ✅ Response time < 10 seconds

4. **Quality:**
   - ✅ No critical bugs
   - ✅ Error messages displayed
   - ✅ Basic logging in place
   - ✅ Code is readable

---

## 🎯 Next Steps After Phase 1

Once Phase 1 is complete:

1. **Review & Demo**
   - Test with different PDFs
   - Ask various questions
   - Note any issues

2. **Prepare for Phase 2**
   - Sign up for Supabase
   - Plan database schema
   - Review Supabase docs

3. **Phase 2 Goals**
   - Add user authentication
   - Move to Supabase
   - Add async processing
   - Improve UI/UX

---

## 📚 Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- LangChain: https://python.langchain.com/
- Qdrant: https://qdrant.tech/documentation/
- Next.js: https://nextjs.org/docs
- shadcn/ui: https://ui.shadcn.com/

### Tutorials
- OpenAI API: https://platform.openai.com/docs
- RAG: https://www.anthropic.com/index/retrieval-augmented-generation
- Embeddings: https://platform.openai.com/docs/guides/embeddings

### Getting Help
- Check API docs at http://localhost:8000/docs
- Review PHASE_1_TASKS.md for detailed steps
- Review IMPLEMENTATION_PLAN.md for overall strategy

---

## 💡 Tips for Success

1. **Start Simple**
   - Don't try to build everything at once
   - Get one piece working, then move on

2. **Test Frequently**
   - Test after each major component
   - Don't wait until the end

3. **Commit Often**
   - Small, frequent commits
   - Clear commit messages

4. **Read Errors**
   - Error messages usually tell you what's wrong
   - Google error messages

5. **Use the Docs**
   - Swagger UI at /docs is your friend
   - Console.log / print() for debugging

6. **Take Breaks**
   - Step away if stuck
   - Fresh eyes help

---

## 🎉 You've Got This!

Phase 1 is the foundation. Take your time, test thoroughly, and don't rush.

Once Phase 1 works, everything else builds on top of it.

Good luck! 🚀
