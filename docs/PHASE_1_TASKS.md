# Phase 1 Detailed Tasks - Basic RAG System

## Overview
**Duration**: 2 weeks (10-15 hours/week part-time, or 1 week full-time)
**Goal**: Working RAG prototype - upload PDF, ask questions, get answers

---

## Week 1: Backend Foundation

### Task Group 1: Environment Setup (2-3 hours)

#### Task 1.1: Create Backend Structure
```bash
# Create directory structure
mkdir -p backend/app/{api/routes,core,services,utils}
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**Files to create:**
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/logging.py`
- `backend/.env`

**Acceptance criteria:**
- [x] Virtual environment created
- [ ] Directory structure matches plan
- [ ] Can activate venv successfully

#### Task 1.2: Install Dependencies
```bash
# In backend/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0

# LangChain and AI
langchain==0.1.0
langchain-openai==0.0.2
openai==1.3.0

# Vector DB
qdrant-client==1.7.0

# Document processing
pdfplumber==0.10.3
pypdf==3.17.1

# Utilities
python-dotenv==1.0.0
httpx==0.25.2
```

```bash
pip install -r requirements.txt
```

**Acceptance criteria:**
- [ ] All packages install without errors
- [ ] Can import FastAPI
- [ ] Can import OpenAI
- [ ] Can import Qdrant client

#### Task 1.3: Configure Environment Variables
```bash
# backend/.env
OPENAI_API_KEY=sk-your-key-here
QDRANT_HOST=localhost
QDRANT_PORT=6333
UPLOAD_DIR=./uploads
CHUNK_SIZE=1024
CHUNK_OVERLAP=128
TOP_K=5
LOG_LEVEL=INFO
```

**Files to create:**
- `backend/app/core/config.py` - Pydantic settings

**Acceptance criteria:**
- [ ] Environment variables load correctly
- [ ] Config validation works
- [ ] Can access config values

#### Task 1.4: Create Basic FastAPI App
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Financial RAG API", version="0.1.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Test:**
```bash
python -m uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
```

**Acceptance criteria:**
- [ ] FastAPI app runs
- [ ] /health endpoint returns 200
- [ ] Swagger UI accessible at /docs
- [ ] CORS configured

#### Task 1.5: Set up Qdrant (via Docker)
```bash
# Start Qdrant
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

**Test connection:**
```python
# backend/app/core/qdrant_client.py
from qdrant_client import QdrantClient
from app.core.config import settings

def get_qdrant_client():
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT
    )
```

**Acceptance criteria:**
- [ ] Qdrant running on port 6333
- [ ] Can connect from Python
- [ ] Dashboard accessible at http://localhost:6333/dashboard

#### Task 1.6: Test OpenAI Connection
```python
# backend/app/services/openai_service.py
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def test_openai_connection():
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input="test"
    )
    return response.data[0].embedding

# Test
if __name__ == "__main__":
    embedding = test_openai_connection()
    print(f"Embedding dimension: {len(embedding)}")
```

**Acceptance criteria:**
- [ ] OpenAI client initializes
- [ ] Can generate test embedding
- [ ] Embedding has 3072 dimensions

---

### Task Group 2: Document Processing (6-8 hours)

#### Task 2.1: Create Upload Endpoint
```python
# backend/app/api/routes/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files allowed")

    # Save file
    upload_dir = Path("./uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "file_path": str(file_path),
        "status": "uploaded"
    }
```

**Test with curl:**
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@sample.pdf"
```

**Acceptance criteria:**
- [ ] Can upload PDF via API
- [ ] File saved to ./uploads directory
- [ ] Returns correct response
- [ ] Validates file type

#### Task 2.2: Implement PDF Text Extraction
```python
# backend/app/services/document_service.py
import pdfplumber
from pathlib import Path

class DocumentService:
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text

    def get_metadata(self, file_path: str) -> dict:
        """Extract PDF metadata."""
        with pdfplumber.open(file_path) as pdf:
            return {
                "num_pages": len(pdf.pages),
                "metadata": pdf.metadata
            }
```

**Test:**
```python
service = DocumentService()
text = service.extract_text_from_pdf("uploads/sample.pdf")
print(f"Extracted {len(text)} characters")
```

**Acceptance criteria:**
- [ ] Extracts text from PDF
- [ ] Handles multi-page PDFs
- [ ] Returns metadata (page count)
- [ ] Handles errors gracefully

#### Task 2.3: Implement Text Chunking
```python
# backend/app/services/chunking_service.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings

class ChunkingService:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_text(self, text: str, metadata: dict = None) -> list[dict]:
        """Split text into chunks with metadata."""
        chunks = self.splitter.split_text(text)

        return [
            {
                "content": chunk,
                "metadata": {
                    **(metadata or {}),
                    "chunk_index": i,
                    "chunk_size": len(chunk)
                }
            }
            for i, chunk in enumerate(chunks)
        ]
```

**Test:**
```python
service = ChunkingService()
chunks = service.chunk_text("Long text here...", {"document_id": "doc1"})
print(f"Created {len(chunks)} chunks")
```

**Acceptance criteria:**
- [ ] Splits text into chunks
- [ ] Respects chunk size limit
- [ ] Includes overlap
- [ ] Preserves metadata
- [ ] Returns list of chunk dicts

#### Task 2.4: Implement Embedding Generation
```python
# backend/app/services/embedding_service.py
from openai import OpenAI
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-large"

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
```

**Test:**
```python
service = EmbeddingService()
embedding = service.generate_embedding("Financial report Q4 2023")
print(f"Embedding dimension: {len(embedding)}")
```

**Acceptance criteria:**
- [ ] Generates embeddings
- [ ] Handles single text
- [ ] Handles batch processing
- [ ] Returns correct dimension (3072)

#### Task 2.5: Implement Vector Storage
```python
# backend/app/services/vector_service.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from uuid import uuid4

class VectorService:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.collection_name = "documents"
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        if self.collection_name not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large
                    distance=Distance.COSINE
                )
            )

    def store_chunks(self, chunks: list[dict], embeddings: list[list[float]]):
        """Store chunks with embeddings in Qdrant."""
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "content": chunk["content"],
                    **chunk["metadata"]
                }
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return len(points)
```

**Acceptance criteria:**
- [ ] Creates Qdrant collection
- [ ] Stores vectors with metadata
- [ ] Handles batch uploads
- [ ] Returns count of stored points

#### Task 2.6: Integration - Complete Document Processing
```python
# backend/app/api/routes/documents.py (updated)
from app.services.document_service import DocumentService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService

@router.post("/upload-and-process")
async def upload_and_process(file: UploadFile = File(...)):
    # 1. Save file
    file_path = save_file(file)

    # 2. Extract text
    doc_service = DocumentService()
    text = doc_service.extract_text_from_pdf(file_path)
    metadata = doc_service.get_metadata(file_path)

    # 3. Chunk text
    chunk_service = ChunkingService()
    chunks = chunk_service.chunk_text(text, {
        "filename": file.filename,
        "num_pages": metadata["num_pages"]
    })

    # 4. Generate embeddings
    embed_service = EmbeddingService()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = embed_service.generate_embeddings_batch(texts)

    # 5. Store in Qdrant
    vector_service = VectorService(qdrant_client)
    num_stored = vector_service.store_chunks(chunks, embeddings)

    return {
        "filename": file.filename,
        "num_pages": metadata["num_pages"],
        "num_chunks": len(chunks),
        "num_stored": num_stored,
        "status": "processed"
    }
```

**Acceptance criteria:**
- [ ] Complete pipeline works end-to-end
- [ ] PDF → text → chunks → embeddings → Qdrant
- [ ] Returns processing statistics
- [ ] Handles errors at each stage

---

### Task Group 3: RAG Query Pipeline (6-8 hours)

#### Task 3.1: Implement Vector Search
```python
# backend/app/services/retrieval_service.py
from qdrant_client import QdrantClient
from app.core.config import settings

class RetrievalService:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.collection_name = "documents"

    def search_similar_chunks(
        self,
        query_embedding: list[float],
        top_k: int = None
    ) -> list[dict]:
        """Search for similar chunks in Qdrant."""
        top_k = top_k or settings.TOP_K

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )

        return [
            {
                "content": hit.payload["content"],
                "score": hit.score,
                "metadata": {
                    k: v for k, v in hit.payload.items()
                    if k != "content"
                }
            }
            for hit in results
        ]
```

**Acceptance criteria:**
- [ ] Searches Qdrant for similar vectors
- [ ] Returns top-k results
- [ ] Includes similarity scores
- [ ] Returns chunk content and metadata

#### Task 3.2: Create Prompt Template
```python
# backend/app/services/prompt_service.py
from langchain.prompts import ChatPromptTemplate

class PromptService:
    def __init__(self):
        self.template = ChatPromptTemplate.from_messages([
            ("system", """You are a financial analyst assistant. Answer questions based ONLY on the provided context from financial documents.

If the context doesn't contain enough information to answer the question, say so clearly.

Always cite your sources using the format: [Document: filename, Page: X]"""),
            ("user", """Context from financial documents:

{context}

Question: {question}

Provide a detailed answer with citations.""")
        ])

    def format_context(self, chunks: list[dict]) -> str:
        """Format retrieved chunks into context."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk["metadata"]
            context_parts.append(
                f"[Source {i}] "
                f"Document: {metadata.get('filename', 'Unknown')}, "
                f"Page: {metadata.get('page', 'N/A')}\n"
                f"{chunk['content']}\n"
            )
        return "\n---\n".join(context_parts)

    def create_prompt(self, question: str, chunks: list[dict]) -> str:
        """Create final prompt with context."""
        context = self.format_context(chunks)
        return self.template.format_messages(
            context=context,
            question=question
        )
```

**Acceptance criteria:**
- [ ] Creates structured prompt
- [ ] Includes system message
- [ ] Formats context from chunks
- [ ] Includes citations instructions

#### Task 3.3: Implement LLM Call
```python
# backend/app/services/llm_service.py
from openai import OpenAI
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"

    def generate_answer(
        self,
        messages: list[dict],
        temperature: float = 0.1
    ) -> dict:
        """Generate answer using GPT-4."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=2048
        )

        return {
            "answer": response.choices[0].message.content,
            "model": response.model,
            "tokens_used": response.usage.total_tokens,
            "finish_reason": response.choices[0].finish_reason
        }
```

**Acceptance criteria:**
- [ ] Calls GPT-4 API
- [ ] Returns generated answer
- [ ] Includes token usage
- [ ] Handles API errors

#### Task 3.4: Create RAG Service (Orchestration)
```python
# backend/app/services/rag_service.py
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.prompt_service import PromptService
from app.services.llm_service import LLMService

class RAGService:
    def __init__(self, qdrant_client):
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService(qdrant_client)
        self.prompt_service = PromptService()
        self.llm_service = LLMService()

    async def query(self, question: str) -> dict:
        """Execute complete RAG pipeline."""
        # 1. Embed query
        query_embedding = self.embedding_service.generate_embedding(question)

        # 2. Search similar chunks
        chunks = self.retrieval_service.search_similar_chunks(query_embedding)

        # 3. Create prompt
        messages = self.prompt_service.create_prompt(question, chunks)

        # 4. Generate answer
        result = self.llm_service.generate_answer(messages)

        # 5. Format response
        return {
            "question": question,
            "answer": result["answer"],
            "sources": [
                {
                    "content": chunk["content"][:200] + "...",
                    "metadata": chunk["metadata"],
                    "score": chunk["score"]
                }
                for chunk in chunks
            ],
            "tokens_used": result["tokens_used"]
        }
```

**Acceptance criteria:**
- [ ] Orchestrates complete RAG flow
- [ ] Query → embedding → search → prompt → LLM
- [ ] Returns answer with sources
- [ ] Handles errors at each step

#### Task 3.5: Create Query Endpoint
```python
# backend/app/api/routes/query.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag_service import RAGService

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict]
    tokens_used: int

@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    if not request.question:
        raise HTTPException(400, "Question cannot be empty")

    rag_service = RAGService(qdrant_client)
    result = await rag_service.query(request.question)

    return result
```

**Test:**
```bash
curl -X POST http://localhost:8000/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the total revenue?"}'
```

**Acceptance criteria:**
- [ ] Query endpoint works
- [ ] Returns answer with sources
- [ ] Validates input
- [ ] Returns proper error messages

#### Task 3.6: Test Complete RAG Pipeline
```python
# test_rag.py
import requests

# 1. Upload document
with open("sample_financial_report.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/documents/upload-and-process",
        files={"file": f}
    )
    print(f"Upload: {response.json()}")

# 2. Wait a moment for processing
import time
time.sleep(2)

# 3. Query
response = requests.post(
    "http://localhost:8000/query/",
    json={"question": "What was the total revenue in 2023?"}
)
result = response.json()
print(f"\nQuestion: {result['question']}")
print(f"Answer: {result['answer']}")
print(f"\nSources: {len(result['sources'])}")
```

**Acceptance criteria:**
- [ ] Can upload PDF and process
- [ ] Can query and get answer
- [ ] Answer includes citations
- [ ] End-to-end flow works

---

## Week 2: Frontend

### Task Group 4: Frontend Setup (3-4 hours)

#### Task 4.1: Create Next.js App
```bash
npx create-next-app@latest frontend --typescript --tailwind --app --no-src
cd frontend
```

**Configuration choices:**
- TypeScript: Yes
- Tailwind CSS: Yes
- App Router: Yes
- Import alias: @/*

**Acceptance criteria:**
- [ ] Next.js app created
- [ ] TypeScript configured
- [ ] Tailwind CSS working
- [ ] Dev server runs

#### Task 4.2: Install shadcn/ui
```bash
npx shadcn-ui@latest init
```

Install components:
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add skeleton
```

**Acceptance criteria:**
- [ ] shadcn/ui configured
- [ ] Components installed
- [ ] Can import and use components

#### Task 4.3: Set Up API Client
```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload-and-process`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  return response.json();
}

export async function queryDocuments(question: string) {
  const response = await fetch(`${API_BASE_URL}/query/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error('Query failed');
  }

  return response.json();
}
```

**Acceptance criteria:**
- [ ] API client functions created
- [ ] Handles errors properly
- [ ] TypeScript types defined

#### Task 4.4: Create Basic Layout
```typescript
// app/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 py-6">
              <h1 className="text-3xl font-bold">Financial RAG System</h1>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
```

**Acceptance criteria:**
- [ ] Layout with header
- [ ] Responsive container
- [ ] Basic styling applied

---

### Task Group 5: Upload UI (4-5 hours)

#### Task 5.1: Create Upload Page
```typescript
// app/upload/page.tsx
'use client'

import { useState } from 'react'
import { uploadDocument } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    try {
      const data = await uploadDocument(file)
      setResult(data)
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Upload Document</h2>

        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mb-4"
        />

        <Button
          onClick={handleUpload}
          disabled={!file || uploading}
        >
          {uploading ? 'Processing...' : 'Upload and Process'}
        </Button>

        {result && (
          <div className="mt-4 p-4 bg-green-50 rounded">
            <p>✓ Processed: {result.filename}</p>
            <p>Pages: {result.num_pages}</p>
            <p>Chunks: {result.num_chunks}</p>
          </div>
        )}
      </Card>
    </div>
  )
}
```

**Acceptance criteria:**
- [ ] Upload page created
- [ ] File input works
- [ ] Upload button functional
- [ ] Shows processing status
- [ ] Displays results

---

### Task Group 6: Chat Interface (6-8 hours)

#### Task 6.1: Create Chat Page
```typescript
// app/chat/page.tsx
'use client'

import { useState } from 'react'
import { queryDocuments } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const result = await queryDocuments(input)

      const assistantMessage: Message = {
        role: 'assistant',
        content: result.answer,
        sources: result.sources
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Query failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="h-[600px] flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 p-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <Card className={`max-w-[80%] p-4 ${msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white'}`}>
                <p>{msg.content}</p>
                {msg.sources && (
                  <div className="mt-2 text-sm opacity-75">
                    <p>Sources: {msg.sources.length} documents</p>
                  </div>
                )}
              </Card>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <Card className="p-4">
                <p>Thinking...</p>
              </Card>
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              Send
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
```

**Acceptance criteria:**
- [ ] Chat interface displayed
- [ ] Can type and send messages
- [ ] Messages appear in chat
- [ ] Shows loading state
- [ ] Displays sources

#### Task 6.2: Add Navigation
```typescript
// components/nav.tsx
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export function Navigation() {
  return (
    <nav className="flex gap-4">
      <Link href="/upload">
        <Button variant="ghost">Upload</Button>
      </Link>
      <Link href="/chat">
        <Button variant="ghost">Chat</Button>
      </Link>
    </nav>
  )
}

// Add to layout.tsx
```

**Acceptance criteria:**
- [ ] Navigation bar created
- [ ] Can navigate between pages
- [ ] Active page highlighted

---

## Testing Checklist

### Backend Tests
- [ ] Health check endpoint works
- [ ] Can upload PDF
- [ ] PDF text extraction works
- [ ] Text chunking produces correct chunks
- [ ] Embeddings generated successfully
- [ ] Vectors stored in Qdrant
- [ ] Query endpoint accepts questions
- [ ] RAG pipeline returns answers
- [ ] Answers include citations

### Frontend Tests
- [ ] App loads without errors
- [ ] Upload page renders
- [ ] Can select file
- [ ] Upload progress shown
- [ ] Chat page renders
- [ ] Can send messages
- [ ] Messages display correctly
- [ ] Loading states work
- [ ] Navigation works

### Integration Tests
- [ ] Upload PDF from frontend → backend processes
- [ ] Ask question from frontend → backend returns answer
- [ ] Error messages display correctly
- [ ] Can upload multiple documents
- [ ] Can ask multiple questions

---

## Success Criteria for Phase 1

At the end of Week 2, you should have:

✅ **Working Backend:**
- FastAPI app running
- Can upload and process PDFs
- Text extraction and chunking working
- Embeddings generated and stored in Qdrant
- Query endpoint returns RAG answers

✅ **Working Frontend:**
- Next.js app running
- Upload page functional
- Chat interface working
- Can communicate with backend

✅ **End-to-End Flow:**
- Upload PDF → Process → Ask question → Get answer
- Complete RAG pipeline working
- Answers include citations from documents

✅ **Quality:**
- No major bugs
- Error handling in place
- Basic logging
- Code is readable

---

## Next Steps After Phase 1

Once Phase 1 is complete, you'll be ready for Phase 2:
- Add Supabase (auth, database, storage)
- Implement async processing with Celery
- Improve UI/UX
- Add user management

But for now, focus on getting the basic RAG system working!

Ready to start? 🚀
