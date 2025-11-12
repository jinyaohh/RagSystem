# Financial RAG System - Development SOP & Guidelines

**For: Claude Code and Human Developers**
**Version:** 1.0.0
**Last Updated:** 2025-11-12
**Phase:** 1 Complete, Phase 2 Pending

---

## Table of Contents

1. [Code Review Findings](#code-review-findings)
2. [System Architecture](#system-architecture)
3. [Development Standards](#development-standards)
4. [File Structure & Organization](#file-structure--organization)
5. [Naming Conventions](#naming-conventions)
6. [API Design Patterns](#api-design-patterns)
7. [Error Handling](#error-handling)
8. [Testing Guidelines](#testing-guidelines)
9. [Configuration Management](#configuration-management)
10. [Common Pitfalls](#common-pitfalls)
11. [Extension Guidelines](#extension-guidelines)
12. [Git Workflow](#git-workflow)
13. [Environment Setup](#environment-setup)
14. [Performance Considerations](#performance-considerations)
15. [Security Best Practices](#security-best-practices)

---

## Code Review Findings

### Phase 1 Implementation Review

#### ✅ Strengths

**Backend:**
1. **Excellent Configuration Management**
   - Type-safe Pydantic Settings with validation
   - Proper enum-based provider selection
   - Environment-specific configuration
   - Clear validation methods

2. **Clean Architecture**
   - Abstract base classes for service interfaces
   - Factory pattern for service creation
   - Dependency injection ready
   - Clear separation of concerns

3. **Comprehensive Error Handling**
   - Try-catch blocks in critical paths
   - Proper logging at all levels
   - Graceful degradation
   - User-friendly error messages

4. **Good Documentation**
   - Docstrings on all public methods
   - Type hints throughout
   - Clear comments for complex logic
   - API endpoint documentation

**Frontend:**
1. **Type Safety**
   - Complete TypeScript coverage
   - Interfaces matching backend API
   - No `any` types used
   - Proper type imports

2. **Component Structure**
   - Clean separation of concerns
   - Reusable UI components
   - Consistent styling with Tailwind
   - Proper state management

3. **User Experience**
   - Loading states
   - Error messages
   - Progress indicators
   - Responsive design

#### ⚠️ Areas for Improvement

**Backend:**

1. **Missing Input Validation (LOW PRIORITY)**
   - Location: `backend/app/services/document_extraction.py`
   - Issue: File size validation happens at API level, but extraction service doesn't double-check
   - Recommendation: Add defensive checks in extraction service
   ```python
   # Add to extract_text():
   if file_path.stat().st_size > settings.MAX_FILE_SIZE:
       raise ValueError(f"File too large: {file_path.stat().st_size} bytes")
   ```

2. **No Rate Limiting (PHASE 2)**
   - Location: API endpoints
   - Issue: No protection against API abuse
   - Recommendation: Add rate limiting middleware in Phase 2
   ```python
   # Future implementation:
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

3. **Limited Error Recovery (PHASE 2)**
   - Location: `backend/app/services/document_processor.py:process_document()`
   - Issue: If embedding fails, entire document processing fails
   - Recommendation: Implement partial success/retry mechanism
   - Status: Acceptable for Phase 1, improve in Phase 2

4. **No Caching (PHASE 3)**
   - Location: RAG query pipeline
   - Issue: Repeated queries re-compute everything
   - Recommendation: Add Redis caching in Phase 3
   - Status: Planned feature, not a bug

**Frontend:**

1. **No Request Cancellation**
   - Location: `frontend/src/lib/api.ts`
   - Issue: Long-running requests can't be cancelled
   - Recommendation: Use AbortController
   ```typescript
   // Add to API functions:
   const controller = new AbortController()
   const response = await fetch(url, { signal: controller.signal })
   ```

2. **Missing Optimistic UI Updates**
   - Location: `frontend/src/app/documents/page.tsx`
   - Issue: Delete operation waits for server response
   - Recommendation: Update UI immediately, rollback on error
   - Priority: LOW (current approach is safer)

3. **No File Upload Progress**
   - Location: `frontend/src/app/upload/page.tsx`
   - Issue: Progress bar is simulated, not real
   - Recommendation: Use XMLHttpRequest or custom fetch wrapper
   - Status: Acceptable for Phase 1

4. **Limited Accessibility**
   - Location: All pages
   - Issue: Missing ARIA labels, keyboard navigation could be better
   - Recommendation: Add accessibility attributes
   - Priority: MEDIUM (should be addressed)

#### 🐛 Bugs Found

**None Critical** - The implementation is production-ready for Phase 1 scope.

**Minor Issues:**

1. **Potential Race Condition (VERY LOW RISK)**
   - Location: `frontend/src/app/chat/page.tsx`
   - Scenario: If user sends multiple messages rapidly, responses could arrive out of order
   - Impact: Unlikely in practice, FastAPI processes sequentially
   - Fix: Add request ID tracking if needed

2. **Missing File Extension Normalization**
   - Location: `backend/app/services/document_extraction.py:_detect_file_type()`
   - Issue: File extensions are case-sensitive
   - Fix Applied: Already handles with `.lower()`
   - Status: ✅ RESOLVED

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js 14)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Home   │  │  Upload  │  │   Chat   │  │Documents │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └─────────────┴──────────────┴─────────────┘          │
│                         │                                    │
│                    API Client                                │
│                  (Type-Safe)                                 │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/JSON
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   API Layer                             │ │
│  │  /api/v1/documents/*  │  /api/v1/query/*  │  /health  │ │
│  └────────────┬────────────────────┬───────────────────────┘ │
│               │                    │                          │
│  ┌────────────▼──────┐  ┌─────────▼──────────────┐          │
│  │ Document Processor │  │    RAG Service         │          │
│  │  - Extraction      │  │  - Retrieval           │          │
│  │  - Chunking        │  │  - Prompting           │          │
│  │  - Embedding       │  │  - Generation          │          │
│  └────────────────────┘  └────────────────────────┘          │
│               │                    │                          │
│  ┌────────────▼──────────┬─────────▼──────────────┐          │
│  │   Service Layer (Abstract Base Classes)        │          │
│  │  - BaseLLMService     - BaseEmbeddingService   │          │
│  │  - BaseVectorService  - Factory Pattern        │          │
│  └──────────┬─────────────────────┬────────────────┘          │
│             │                     │                           │
│  ┌──────────▼──────┐   ┌──────────▼──────────┐              │
│  │ LLM Providers    │   │  Vector DB          │              │
│  │ - OpenAI         │   │  - Qdrant           │              │
│  │ - Anthropic      │   │                     │              │
│  └──────────────────┘   └─────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Core Design Patterns

1. **Abstract Factory Pattern**
   - Purpose: Create service instances based on configuration
   - Location: `backend/app/services/factory.py`
   - Benefits: Easy to swap providers without code changes

2. **Strategy Pattern**
   - Purpose: Different chunking strategies
   - Location: `backend/app/services/chunking.py`
   - Benefits: Flexible text processing

3. **Pipeline Pattern**
   - Purpose: Document processing flow
   - Location: `backend/app/services/document_processor.py`
   - Benefits: Clear, sequential operations

4. **Repository Pattern (Implicit)**
   - Purpose: Vector storage abstraction
   - Location: `backend/app/services/vector/*`
   - Benefits: Can swap vector DBs easily

### Data Flow

#### Document Upload Flow
```
User uploads file
  → Frontend: Validate file type/size
  → API: POST /api/v1/documents/upload-and-process
  → Save file to disk
  → Extract text (PDF/DOCX/XLSX/TXT)
  → Chunk text (configurable strategy)
  → Generate embeddings (OpenAI/Local)
  → Store vectors in Qdrant
  → Return processing stats
```

#### RAG Query Flow
```
User asks question
  → Frontend: POST /api/v1/query
  → Embed question
  → Vector search (top-k similar chunks)
  → Format prompt with context
  → Generate answer with LLM
  → Format response with sources
  → Return to user
```

---

## Development Standards

### Python (Backend)

#### Code Style
- **Formatter:** Black (line length: 100)
- **Linter:** Ruff
- **Type Checker:** mypy (strict mode)
- **Import Order:** isort (black-compatible)

#### Standards
```python
# ✅ GOOD: Type hints, docstrings, descriptive names
async def process_document(
    self,
    file_path: Path,
    document_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process a document through the RAG pipeline.

    Args:
        file_path: Path to the uploaded file
        document_id: Optional custom document ID
        metadata: Optional metadata to attach

    Returns:
        Processing result with statistics

    Raises:
        ValueError: If file format is unsupported
        IOError: If file cannot be read
    """
    logger.info(f"Processing document: {file_path}")
    # Implementation...

# ❌ BAD: No types, no docs, unclear naming
async def proc(p, d=None, m=None):
    # Do stuff
    return result
```

#### Logging
```python
# ✅ GOOD: Structured logging with context
logger.info(f"Processing document: {doc_id}")
logger.debug(f"Extracted {len(chunks)} chunks")
logger.error(f"Failed to process {doc_id}: {e}", exc_info=True)

# ❌ BAD: Print statements
print("Processing...")
print(f"Error: {e}")
```

#### Error Handling
```python
# ✅ GOOD: Specific exceptions, proper logging, graceful degradation
try:
    result = await self.risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    return {
        'status': 'failed',
        'error': str(e),
        'fallback': self.get_default_result()
    }

# ❌ BAD: Bare except, swallowing errors
try:
    result = await self.risky_operation()
except:
    pass
```

### TypeScript (Frontend)

#### Code Style
- **Formatter:** Prettier (built into Next.js)
- **Linter:** ESLint (Next.js config)
- **Type Checker:** TypeScript strict mode

#### Standards
```typescript
// ✅ GOOD: Explicit types, JSDoc, proper error handling
/**
 * Query documents using RAG system.
 *
 * @param request - Query request with question and options
 * @returns Query response with answer and sources
 * @throws APIError if request fails
 */
export async function queryDocuments(
  request: QueryRequest
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse<QueryResponse>(response)
}

// ❌ BAD: No types, any usage
export async function query(req: any): Promise<any> {
  const res = await fetch(url, { body: req })
  return res.json()
}
```

#### React Component Standards
```typescript
// ✅ GOOD: Typed props, proper hooks, error states
interface UploadPageProps {
  maxFileSize?: number
  allowedTypes?: string[]
}

export default function UploadPage({
  maxFileSize = 50 * 1024 * 1024,
  allowedTypes = ['pdf', 'docx', 'xlsx', 'txt']
}: UploadPageProps) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Implementation...
}

// ❌ BAD: No types, inline styles, no error handling
export default function Upload() {
  const [file, setFile] = useState(null)

  return <div style={{margin: 10}}>...</div>
}
```

---

## File Structure & Organization

### Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, lifespan, CORS
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic Settings (SINGLE SOURCE OF TRUTH)
│   │   └── logging.py             # Logging configuration
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── documents.py       # Document upload/management
│   │       └── query.py           # RAG query endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base classes
│   │   ├── factory.py             # Service factory functions
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── openai_service.py
│   │   │   └── anthropic_service.py
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   └── openai_service.py
│   │   ├── vector/
│   │   │   ├── __init__.py
│   │   │   └── qdrant_service.py
│   │   ├── document_extraction.py
│   │   ├── chunking.py
│   │   ├── document_processor.py
│   │   ├── retrieval.py
│   │   ├── prompts.py
│   │   └── rag.py
│   └── models/                    # Pydantic models (future)
├── tests/                         # Tests mirror app structure
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
└── README.md
```

### Frontend Structure

```
frontend/
├── src/
│   ├── app/                       # Next.js 14 App Router
│   │   ├── layout.tsx             # Root layout with header/footer
│   │   ├── page.tsx               # Home page
│   │   ├── globals.css            # Global styles + Tailwind
│   │   ├── chat/
│   │   │   └── page.tsx           # Chat interface
│   │   ├── upload/
│   │   │   └── page.tsx           # Document upload
│   │   └── documents/
│   │       └── page.tsx           # Document management
│   ├── components/
│   │   └── ui/                    # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       └── progress.tsx
│   ├── lib/
│   │   ├── api.ts                 # API client (all backend calls)
│   │   └── utils.ts               # Helper functions
│   └── types/
│       └── index.ts               # TypeScript types
├── public/                        # Static assets
├── .env.local                     # Environment variables (gitignored)
├── .env.example                   # Environment template
├── next.config.js                 # Next.js config
├── tailwind.config.ts             # Tailwind config
├── tsconfig.json                  # TypeScript config
├── package.json                   # Node dependencies
└── README.md
```

### File Naming Rules

**Backend:**
- Services: `{name}_service.py` (e.g., `openai_service.py`)
- Routes: `{resource}.py` (e.g., `documents.py`, `query.py`)
- Config: Always `config.py`
- Tests: `test_{module}.py`

**Frontend:**
- Pages: `page.tsx` (Next.js App Router convention)
- Components: PascalCase (e.g., `Button.tsx`, `DocumentCard.tsx`)
- Utils: camelCase (e.g., `api.ts`, `utils.ts`)
- Types: `index.ts` or `{feature}.types.ts`

---

## Naming Conventions

### Python

#### Variables & Functions
```python
# ✅ GOOD: snake_case, descriptive
document_id = "abc123"
chunk_size = 1024
embedding_dimension = 3072

async def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF file."""
    pass

async def get_document_by_id(document_id: str) -> Optional[Document]:
    """Retrieve document by ID."""
    pass

# ❌ BAD: camelCase, unclear names
documentId = "abc123"
sz = 1024

async def getPDF(fp):
    pass
```

#### Classes
```python
# ✅ GOOD: PascalCase, descriptive
class DocumentProcessor:
    pass

class OpenAILLMService(BaseLLMService):
    pass

class RAGService:
    pass

# ❌ BAD: snake_case, abbreviations
class doc_processor:
    pass

class OAIS:  # What does this mean?
    pass
```

#### Constants
```python
# ✅ GOOD: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 52428800
DEFAULT_CHUNK_SIZE = 1024
SUPPORTED_FILE_TYPES = ["pdf", "docx", "xlsx", "txt"]

# ❌ BAD: lowercase
max_file_size = 52428800
```

#### Environment Variables
```python
# ✅ GOOD: UPPER_SNAKE_CASE, prefixed by category
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4-turbo-preview"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
LLM_PROVIDER = "openai"

# ❌ BAD: Mixed case, no grouping
openAI_key = "sk-..."
model = "gpt-4"
host = "localhost"
```

### TypeScript

#### Variables & Functions
```typescript
// ✅ GOOD: camelCase, descriptive
const documentId = 'abc123'
const chunkSize = 1024

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  // Implementation
}

export function formatBytes(bytes: number, decimals: number = 2): string {
  // Implementation
}

// ❌ BAD: snake_case, unclear
const document_id = 'abc123'

export async function upload(f: any): Promise<any> {
  // Implementation
}
```

#### Types & Interfaces
```typescript
// ✅ GOOD: PascalCase, descriptive
interface QueryRequest {
  question: string
  topK?: number
  includeSources?: boolean
}

type DocumentStatus = 'processing' | 'completed' | 'failed'

interface APIResponse<T> {
  data: T
  status: number
}

// ❌ BAD: camelCase, vague names
interface request {
  q: string
  k?: number
}

type Status = string
```

#### React Components
```typescript
// ✅ GOOD: PascalCase, descriptive file and function names
// File: UploadPage.tsx
export default function UploadPage() {
  return <div>...</div>
}

// File: DocumentCard.tsx
interface DocumentCardProps {
  document: Document
  onDelete: (id: string) => void
}

export function DocumentCard({ document, onDelete }: DocumentCardProps) {
  return <div>...</div>
}

// ❌ BAD: Mismatched names
// File: upload.tsx
export default function Component() {
  return <div>...</div>
}
```

---

## API Design Patterns

### RESTful Conventions

```
Resource: documents
GET    /api/v1/documents           # List all documents
POST   /api/v1/documents/upload    # Upload a document
POST   /api/v1/documents/upload-and-process  # Upload + process
GET    /api/v1/documents/{id}      # Get document by ID
DELETE /api/v1/documents/{id}      # Delete document

Resource: query
POST   /api/v1/query               # Query documents (POST because of body)
POST   /api/v1/query/batch         # Batch queries
POST   /api/v1/query/summarize     # Summarize document
POST   /api/v1/query/compare       # Compare documents

Health:
GET    /health                     # Simple health check
GET    /health/detailed            # Detailed system status
```

### Request/Response Models

**Always use Pydantic models for requests and responses:**

```python
# ✅ GOOD: Typed request/response models
class QueryRequest(BaseModel):
    """Request model for queries."""
    question: str = Field(..., min_length=1, description="Question to ask")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks")
    include_sources: Optional[bool] = Field(None, description="Include citations")

class QueryResponse(BaseModel):
    """Response model for queries."""
    question: str
    answer: str
    status: str
    response_time_ms: int
    sources: Optional[List[dict]] = None

@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    # Implementation
    pass

# ❌ BAD: Dict-based, no validation
@router.post("/")
async def query(data: dict) -> dict:
    question = data.get("question")
    # No validation, type safety, or documentation
    pass
```

### Error Responses

**Standard error format:**

```python
# ✅ GOOD: Consistent error responses
from fastapi import HTTPException, status

# 400 Bad Request - Client error
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid file type. Allowed: pdf, docx, xlsx, txt"
)

# 404 Not Found - Resource doesn't exist
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Document {document_id} not found"
)

# 500 Internal Server Error - Server error
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to process document. Please try again."
)

# ❌ BAD: Generic errors
raise Exception("Error!")
```

### Status Codes

```python
# ✅ Use appropriate status codes
200 OK                  # Successful GET, PUT, PATCH
201 Created             # Successful POST (resource created)
204 No Content          # Successful DELETE
400 Bad Request         # Invalid input
401 Unauthorized        # Authentication required
403 Forbidden           # Not allowed
404 Not Found           # Resource doesn't exist
422 Unprocessable       # Validation failed (Pydantic)
500 Internal Server     # Server error
503 Service Unavailable # Dependency (LLM, DB) down
```

---

## Error Handling

### Backend Error Handling

#### Service Layer
```python
# ✅ GOOD: Catch specific exceptions, log, return structured result
async def process_document(self, file_path: Path) -> Dict[str, Any]:
    """Process document with comprehensive error handling."""
    try:
        # Attempt processing
        text = await self.extract_text(file_path)
        chunks = await self.chunk_text(text)
        embeddings = await self.generate_embeddings(chunks)

        return {
            'status': 'success',
            'chunks_created': len(chunks),
            'vectors_stored': len(embeddings)
        }

    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}", exc_info=True)
        return {
            'status': 'failed',
            'error': 'File not found',
            'error_type': 'FileNotFoundError'
        }

    except ValueError as e:
        logger.error(f"Invalid file format: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'error_type': 'ValueError'
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': 'An unexpected error occurred',
            'error_type': type(e).__name__
        }

# ❌ BAD: Bare except, no logging
async def process_document(self, file_path):
    try:
        # Processing
        pass
    except:
        return {'status': 'error'}
```

#### API Layer
```python
# ✅ GOOD: Let FastAPI handle HTTP exceptions, log errors
@router.post("/upload-and-process")
async def upload_and_process_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    try:
        # Validate file
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.content_type}"
            )

        # Process document
        result = await document_processor.process_document(file_path)

        if result['status'] == 'failed':
            logger.warning(f"Processing failed: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.get('error', 'Processing failed')
            )

        return DocumentProcessingResult(**result)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )

# ❌ BAD: Swallow all errors
@router.post("/upload")
async def upload(file: UploadFile):
    try:
        # Process
        return {"status": "ok"}
    except:
        return {"status": "error"}
```

### Frontend Error Handling

```typescript
// ✅ GOOD: Custom error class, user-friendly messages
class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'APIError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`
    let detail: string | undefined

    try {
      const errorData = await response.json()
      detail = errorData.detail || errorData.message
      if (detail) {
        errorMessage = detail
      }
    } catch {
      // Couldn't parse error JSON, use status text
    }

    throw new APIError(errorMessage, response.status, detail)
  }

  return response.json()
}

// Component usage
export default function UploadPage() {
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async () => {
    setError(null)

    try {
      const result = await uploadAndProcessDocument(file)
      setResult(result)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred')
      }
      logger.error('Upload failed:', err)
    }
  }

  return (
    <div>
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      {/* Rest of component */}
    </div>
  )
}

// ❌ BAD: No error handling
const handleUpload = async () => {
  const result = await uploadDocument(file)
  setResult(result)
}
```

---

## Testing Guidelines

### Backend Testing (Phase 2)

```python
# tests/test_services/test_chunking.py
import pytest
from app.services.chunking import ChunkingService

class TestChunkingService:
    """Test suite for ChunkingService."""

    @pytest.fixture
    def chunking_service(self):
        """Create ChunkingService instance."""
        return ChunkingService(chunk_size=100, chunk_overlap=20)

    def test_chunk_text_simple(self, chunking_service):
        """Test basic text chunking."""
        text = "A" * 250
        chunks = chunking_service.chunk_text(text)

        assert len(chunks) > 1
        assert all(len(chunk['content']) <= 100 for chunk in chunks)

    def test_chunk_text_empty(self, chunking_service):
        """Test chunking empty text."""
        chunks = chunking_service.chunk_text("")
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_chunk_with_metadata(self, chunking_service):
        """Test chunking with metadata preservation."""
        text = "Sample text"
        metadata = {'doc_id': '123', 'page': 1}

        chunks = chunking_service.chunk_text(text, metadata=metadata)

        assert all(chunk['metadata']['doc_id'] == '123' for chunk in chunks)
```

### Frontend Testing (Phase 2)

```typescript
// __tests__/lib/api.test.ts
import { queryDocuments } from '@/lib/api'
import { QueryRequest, QueryResponse } from '@/types'

describe('API Client', () => {
  beforeEach(() => {
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('queryDocuments', () => {
    it('should send query and return response', async () => {
      const mockResponse: QueryResponse = {
        question: 'What is revenue?',
        answer: '$1M',
        status: 'completed',
        response_time_ms: 1000
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const request: QueryRequest = {
        question: 'What is revenue?',
        top_k: 5
      }

      const result = await queryDocuments(request)

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/query'),
        expect.objectContaining({
          method: 'POST'
        })
      )
    })

    it('should throw APIError on failure', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'Invalid question' })
      })

      const request: QueryRequest = {
        question: '',
        top_k: 5
      }

      await expect(queryDocuments(request)).rejects.toThrow('Invalid question')
    })
  })
})
```

---

## Configuration Management

### Backend Configuration Rules

1. **Single Source of Truth:** `backend/app/core/config.py`
2. **Environment Variables:** `.env` file (never commit!)
3. **Type Safety:** Pydantic Settings with validation
4. **Provider Flexibility:** Enum-based selection

```python
# ✅ GOOD: Use settings object everywhere
from app.core.config import settings

class OpenAILLMService(BaseLLMService):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE

# ❌ BAD: Hardcoded values
class OpenAILLMService:
    def __init__(self):
        self.api_key = "sk-hardcoded"
        self.model = "gpt-4"
```

### Environment Variable Naming

```bash
# ✅ GOOD: Grouped, descriptive, UPPER_SNAKE_CASE
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.1

# Embedding Configuration
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=financial_documents

# ❌ BAD: No grouping, inconsistent naming
api_key=sk-...
model=gpt-4
db_host=localhost
```

### Frontend Configuration

```typescript
// ✅ GOOD: Use environment variables with defaults
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || 'Financial RAG System'

// ❌ BAD: Hardcoded values
const API_BASE_URL = 'http://localhost:8000'
```

**Note:** Next.js requires `NEXT_PUBLIC_` prefix for client-side variables!

---

## Common Pitfalls

### Backend Pitfalls

#### 1. Forgetting to Await Async Functions
```python
# ❌ BAD: Missing await
async def process_document(self):
    result = self.async_function()  # Returns coroutine, not result!
    return result

# ✅ GOOD: Proper await
async def process_document(self):
    result = await self.async_function()
    return result
```

#### 2. Mutating Configuration
```python
# ❌ BAD: Modifying settings
from app.core.config import settings
settings.CHUNK_SIZE = 2048  # Don't do this!

# ✅ GOOD: Override in function call
chunk_service = ChunkingService(chunk_size=2048)
```

#### 3. Not Validating Input
```python
# ❌ BAD: No validation
@router.post("/query")
async def query(question: str):
    result = await rag_service.query(question)
    return result

# ✅ GOOD: Pydantic validation
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)

@router.post("/query")
async def query(request: QueryRequest):
    result = await rag_service.query(request.question, top_k=request.top_k)
    return result
```

#### 4. Logging Secrets
```python
# ❌ BAD: Logging API keys
logger.info(f"Using API key: {settings.OPENAI_API_KEY}")

# ✅ GOOD: Mask secrets
logger.info(f"Using API key: {settings.OPENAI_API_KEY[:7]}...")
```

#### 5. Synchronous I/O in Async Functions
```python
# ❌ BAD: Blocking I/O
async def process_file(file_path: Path):
    with open(file_path, 'r') as f:  # Blocks event loop!
        content = f.read()
    return content

# ✅ GOOD: Use aiofiles or run_in_executor
import aiofiles

async def process_file(file_path: Path):
    async with aiofiles.open(file_path, 'r') as f:
        content = await f.read()
    return content
```

### Frontend Pitfalls

#### 1. Missing Dependency Arrays
```typescript
// ❌ BAD: Runs on every render
useEffect(() => {
  fetchData()
})

// ✅ GOOD: Runs once on mount
useEffect(() => {
  fetchData()
}, [])

// ✅ GOOD: Runs when dependency changes
useEffect(() => {
  fetchData(documentId)
}, [documentId])
```

#### 2. Not Handling Loading States
```typescript
// ❌ BAD: No loading indicator
const handleSubmit = async () => {
  const result = await submitForm()
  setResult(result)
}

// ✅ GOOD: Show loading state
const handleSubmit = async () => {
  setLoading(true)
  try {
    const result = await submitForm()
    setResult(result)
  } finally {
    setLoading(false)
  }
}
```

#### 3. Using Any Type
```typescript
// ❌ BAD: Loses type safety
const handleData = (data: any) => {
  console.log(data.someField)  // No autocomplete, no type checking
}

// ✅ GOOD: Proper types
interface ResponseData {
  someField: string
  anotherField: number
}

const handleData = (data: ResponseData) => {
  console.log(data.someField)  // Type-safe!
}
```

#### 4. Inline Anonymous Functions in JSX
```typescript
// ❌ BAD: Creates new function on every render
<Button onClick={() => handleClick(item.id)}>Click</Button>

// ✅ GOOD: Use useCallback or define outside render
const handleItemClick = useCallback((id: string) => {
  handleClick(id)
}, [handleClick])

<Button onClick={() => handleItemClick(item.id)}>Click</Button>
```

---

## Extension Guidelines

### Adding a New LLM Provider

**Example: Adding Google Gemini**

1. **Create Service Class** (`backend/app/services/llm/gemini_service.py`)
```python
from app.services.base import BaseLLMService, Message, LLMResponse
from app.core.config import settings
import google.generativeai as genai

class GeminiLLMService(BaseLLMService):
    """Google Gemini LLM service."""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate response using Gemini."""
        # Convert messages to Gemini format
        prompt = self._format_messages(messages)

        # Generate
        response = await self.model.generate_content_async(prompt)

        return LLMResponse(
            content=response.text,
            model=settings.GEMINI_MODEL,
            tokens_used=response.usage_metadata.total_token_count,
            finish_reason="stop"
        )

    def get_model_name(self) -> str:
        return settings.GEMINI_MODEL

    def _format_messages(self, messages: List[Message]) -> str:
        # Implementation
        pass
```

2. **Update Config** (`backend/app/core/config.py`)
```python
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"  # Add new provider
    LOCAL = "local"

class Settings(BaseSettings):
    # ... existing settings ...

    # Gemini Configuration
    GEMINI_API_KEY: str = "placeholder"
    GEMINI_MODEL: str = "gemini-pro"
    GEMINI_TEMPERATURE: float = 0.1
```

3. **Update Factory** (`backend/app/services/factory.py`)
```python
from app.services.llm.gemini_service import GeminiLLMService

def create_llm_service(provider: Optional[LLMProvider] = None) -> BaseLLMService:
    provider = provider or settings.LLM_PROVIDER

    if provider == LLMProvider.OPENAI:
        return OpenAILLMService()
    elif provider == LLMProvider.ANTHROPIC:
        return AnthropicLLMService()
    elif provider == LLMProvider.GEMINI:
        return GeminiLLMService()  # Add new case
    elif provider == LLMProvider.LOCAL:
        return LocalLLMService()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
```

4. **Update .env.example**
```bash
# Google Gemini
GEMINI_API_KEY=placeholder
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.1
```

5. **Test the Integration**
```python
# Set LLM_PROVIDER=gemini in .env
# Run: python -m app.main
# Verify health check shows Gemini
```

### Adding a New API Endpoint

**Example: Adding Document Statistics Endpoint**

1. **Create Route** (`backend/app/api/routes/documents.py`)
```python
@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_statistics() -> DocumentStatsResponse:
    """
    Get statistics about uploaded documents.

    Returns:
        Statistics including total count, size, types, etc.
    """
    # Get all documents
    documents = await list_all_documents()

    # Calculate stats
    total_count = len(documents)
    total_size = sum(doc.file_size for doc in documents)
    file_types = Counter(doc.file_type for doc in documents)

    return DocumentStatsResponse(
        total_documents=total_count,
        total_size_bytes=total_size,
        file_type_distribution=dict(file_types),
        upload_date_range={
            'earliest': min(doc.upload_date for doc in documents) if documents else None,
            'latest': max(doc.upload_date for doc in documents) if documents else None,
        }
    )
```

2. **Add Response Model**
```python
class DocumentStatsResponse(BaseModel):
    """Response model for document statistics."""
    total_documents: int
    total_size_bytes: int
    file_type_distribution: Dict[str, int]
    upload_date_range: Dict[str, Optional[datetime]]
```

3. **Update Frontend Types** (`frontend/src/types/index.ts`)
```typescript
export interface DocumentStatsResponse {
  total_documents: number
  total_size_bytes: number
  file_type_distribution: Record<string, number>
  upload_date_range: {
    earliest: string | null
    latest: string | null
  }
}
```

4. **Add API Client Function** (`frontend/src/lib/api.ts`)
```typescript
export async function getDocumentStatistics(): Promise<DocumentStatsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/stats`)
  return handleResponse(response)
}
```

5. **Use in Component**
```typescript
const [stats, setStats] = useState<DocumentStatsResponse | null>(null)

useEffect(() => {
  const fetchStats = async () => {
    const data = await getDocumentStatistics()
    setStats(data)
  }
  fetchStats()
}, [])
```

---

## Git Workflow

### Branch Naming

```bash
# ✅ GOOD: Descriptive, categorized
feature/add-gemini-provider
fix/document-upload-validation
refactor/service-factory
docs/update-readme
test/add-chunking-tests

# ❌ BAD: Vague, no category
new-feature
fix
update
```

### Commit Messages

```bash
# ✅ GOOD: Clear, descriptive, follows convention
git commit -m "feat: Add Gemini LLM provider support

- Implement GeminiLLMService with async generation
- Add configuration for Gemini API key and model
- Update factory to include Gemini provider
- Add tests for Gemini service

Closes #123"

# ✅ GOOD: Small, focused commits
git commit -m "fix: Handle empty query in RAG service"
git commit -m "docs: Update API documentation for query endpoint"
git commit -m "refactor: Extract prompt formatting to separate method"

# ❌ BAD: Vague, no context
git commit -m "updates"
git commit -m "fix bug"
git commit -m "WIP"
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `test`: Add/update tests
- `chore`: Maintenance tasks
- `perf`: Performance improvement
- `style`: Code style changes

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/add-new-feature
   ```

2. **Make Changes with Small Commits**
   ```bash
   git add <files>
   git commit -m "feat: Add initial implementation"
   git commit -m "test: Add unit tests"
   git commit -m "docs: Update documentation"
   ```

3. **Push to Remote**
   ```bash
   git push -u origin feature/add-new-feature
   ```

4. **Create Pull Request**
   - Clear title and description
   - Reference related issues
   - Include testing steps
   - Add screenshots for UI changes

5. **Code Review**
   - Address review comments
   - Push additional commits
   - Re-request review

6. **Merge**
   - Squash commits if needed
   - Delete branch after merge

---

## Environment Setup

### Backend Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd RagSystem/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your API keys
# OPENAI_API_KEY=sk-your-actual-key
# ANTHROPIC_API_KEY=sk-ant-your-actual-key

# 6. Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# 7. Run backend
python -m uvicorn app.main:app --reload

# Backend runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd RagSystem/frontend

# 2. Install dependencies
npm install

# 3. Copy environment template
cp .env.example .env.local

# 4. Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 5. Run development server
npm run dev

# Frontend runs at http://localhost:3000
```

### Docker Setup (Future)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    depends_on:
      - qdrant

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file:
      - ./frontend/.env.local

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
```

---

## Performance Considerations

### Backend Performance

#### 1. Use Async Throughout
```python
# ✅ GOOD: Async all the way
async def process_document(self, file_path: Path):
    text = await self.extract_text(file_path)
    chunks = await self.chunk_text(text)
    embeddings = await self.generate_embeddings(chunks)
    await self.store_vectors(embeddings)

# ❌ BAD: Mixing sync and async
async def process_document(self, file_path: Path):
    text = self.extract_text_sync(file_path)  # Blocks!
    chunks = await self.chunk_text(text)
```

#### 2. Batch Operations
```python
# ✅ GOOD: Batch embeddings
async def generate_embeddings(self, texts: List[str]):
    # Process in batches of 100
    for i in range(0, len(texts), 100):
        batch = texts[i:i+100]
        embeddings = await self.embedding_service.batch_embed(batch)
        yield embeddings

# ❌ BAD: One at a time
async def generate_embeddings(self, texts: List[str]):
    embeddings = []
    for text in texts:
        emb = await self.embedding_service.embed(text)
        embeddings.append(emb)
```

#### 3. Connection Pooling
```python
# ✅ GOOD: Reuse connections
from qdrant_client import QdrantClient

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST)
        # Client manages connection pool

# ❌ BAD: New connection each time
async def search(self, query):
    client = QdrantClient(host=settings.QDRANT_HOST)
    results = client.search(...)
    client.close()
```

### Frontend Performance

#### 1. Memoization
```typescript
// ✅ GOOD: Memoize expensive computations
const sortedDocuments = useMemo(() => {
  return documents.sort((a, b) =>
    new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime()
  )
}, [documents])

// ❌ BAD: Re-sort on every render
const sortedDocuments = documents.sort(...)
```

#### 2. Debouncing
```typescript
// ✅ GOOD: Debounce search input
import { debounce } from 'lodash'

const debouncedSearch = useCallback(
  debounce((query: string) => {
    performSearch(query)
  }, 300),
  []
)

// ❌ BAD: Search on every keystroke
const handleInputChange = (e) => {
  performSearch(e.target.value)
}
```

#### 3. Lazy Loading
```typescript
// ✅ GOOD: Load pages on demand
import dynamic from 'next/dynamic'

const ChatPage = dynamic(() => import('@/app/chat/page'), {
  loading: () => <LoadingSpinner />
})

// ❌ BAD: Import everything upfront
import ChatPage from '@/app/chat/page'
```

---

## Security Best Practices

### 1. API Keys
```python
# ✅ GOOD: Environment variables, never commit
OPENAI_API_KEY=sk-...  # In .env (gitignored)

from app.core.config import settings
api_key = settings.OPENAI_API_KEY

# ❌ BAD: Hardcoded
api_key = "sk-hardcoded-key-here"
```

### 2. Input Validation
```python
# ✅ GOOD: Validate and sanitize
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        # Remove potentially harmful characters
        sanitized = v.strip()
        if not sanitized:
            raise ValueError("Question cannot be empty")
        return sanitized

# ❌ BAD: No validation
@router.post("/query")
async def query(question: str):
    # Directly use user input
    result = execute_query(question)
```

### 3. File Upload Security
```python
# ✅ GOOD: Validate type, size, content
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

async def validate_file(file: UploadFile):
    # Check extension
    ext = file.filename.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type: {ext}")

    # Check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File too large")

    # Check magic bytes (file signature)
    if ext == 'pdf' and not content.startswith(b'%PDF'):
        raise ValueError("Invalid PDF file")

    await file.seek(0)  # Reset for reading

# ❌ BAD: Trust user input
async def upload(file: UploadFile):
    content = await file.read()
    with open(f"uploads/{file.filename}", 'wb') as f:
        f.write(content)
```

### 4. CORS Configuration
```python
# ✅ GOOD: Specific origins
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ❌ BAD: Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Don't do this in production!
)
```

### 5. Rate Limiting (Phase 2)
```python
# ✅ GOOD: Protect endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/query")
@limiter.limit("10/minute")
async def query_documents(request: Request):
    # Only 10 requests per minute per IP
    pass

# ❌ BAD: No rate limiting
@router.post("/query")
async def query_documents():
    # Vulnerable to abuse
    pass
```

---

## Quick Reference

### Most Common Commands

**Backend:**
```bash
# Run server
python -m uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/ tests/

# Type check
mypy app/

# Lint
ruff check app/
```

**Frontend:**
```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check

# Lint
npm run lint
```

### Most Used Imports

**Backend:**
```python
# Core
from app.core.config import settings
from app.services.factory import get_llm_service, get_embedding_service

# FastAPI
from fastapi import APIRouter, HTTPException, status, File, UploadFile
from pydantic import BaseModel, Field

# Logging
import logging
logger = logging.getLogger(__name__)

# Typing
from typing import Dict, List, Optional, Any
```

**Frontend:**
```typescript
// React
import { useState, useEffect, useCallback, useMemo } from 'react'

// Next.js
import Link from 'next/link'
import { useRouter } from 'next/navigation'

// API & Types
import { queryDocuments, uploadDocument } from '@/lib/api'
import type { QueryResponse, Document } from '@/types'

// Components
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
```

---

## Contact & Support

**For Claude Code Users:**
- This document should be your **primary reference** when working on this codebase
- Follow the patterns and conventions established here
- When in doubt, check existing implementations in similar modules

**For Human Developers:**
- GitHub Issues: Report bugs and feature requests
- Pull Requests: Follow the PR template and guidelines
- Documentation: Update this file when adding new patterns

---

**End of SOP Document**

*Last Updated: 2025-11-12*
*Phase 1 Complete - Ready for Phase 2 Development*
