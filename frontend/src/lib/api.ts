/**
 * API Client for Financial RAG Backend
 *
 * Provides typed API calls to the FastAPI backend.
 */

import {
  DocumentUploadResponse,
  DocumentProcessingResult,
  Document,
  QueryRequest,
  QueryResponse,
  HealthResponse,
  AuthResponse,
  SignupRequest,
  LoginRequest,
  User,
  ProcessingJob,
  JobListResponse,
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

// ============================================================================
// Health API
// ============================================================================

export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`)
  return handleResponse(response)
}

export async function detailedHealthCheck(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health/detailed`)
  return handleResponse(response)
}

// ============================================================================
// Document API
// ============================================================================

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    method: 'POST',
    body: formData,
  })

  return handleResponse(response)
}

export async function uploadAndProcessDocument(
  file: File,
  onProgress?: (progress: number) => void
): Promise<DocumentProcessingResult> {
  const formData = new FormData()
  formData.append('file', file)

  // Note: Progress tracking would require XMLHttpRequest or a custom fetch wrapper
  // For now, we'll use a simple fetch
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload-and-process`, {
    method: 'POST',
    body: formData,
  })

  return handleResponse(response)
}

export async function processDocument(documentId: string): Promise<DocumentProcessingResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/process/${documentId}`,
    {
      method: 'POST',
    }
  )

  return handleResponse(response)
}

export async function listDocuments(): Promise<{ documents: Document[]; total: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/`)
  return handleResponse(response)
}

export async function deleteDocument(documentId: string): Promise<{
  document_id: string
  status: string
  message: string
  file_deleted: boolean
  vectors_deleted: boolean
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
    method: 'DELETE',
  })

  return handleResponse(response)
}

export async function getSupportedFormats(): Promise<{
  supported_formats: string[]
  max_file_size_bytes: number
  max_file_size_mb: number
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/supported-formats`)
  return handleResponse(response)
}

// ============================================================================
// Query API
// ============================================================================

export async function queryDocuments(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  return handleResponse(response)
}

export async function batchQuery(
  questions: string[],
  options?: {
    top_k?: number
    include_sources?: boolean
  }
): Promise<QueryResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query/batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      questions,
      ...options,
    }),
  })

  return handleResponse(response)
}

export async function summarizeDocument(
  documentId: string,
  maxLength?: number
): Promise<{
  document_id: string
  summary: string
  status: string
  num_chunks: number
  tokens_used: number
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query/summarize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_id: documentId,
      max_length: maxLength,
    }),
  })

  return handleResponse(response)
}

export async function compareDocuments(
  query: string,
  documentIdA: string,
  documentIdB: string,
  labelA: string = 'Document A',
  labelB: string = 'Document B'
): Promise<{
  query: string
  comparison: string
  status: string
  documents: Record<string, { label: string; num_chunks: number }>
  tokens_used: number
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      document_id_a: documentIdA,
      document_id_b: documentIdB,
      label_a: labelA,
      label_b: labelB,
    }),
  })

  return handleResponse(response)
}

export async function getQueryServiceInfo(): Promise<{
  retrieval: {
    top_k: number
    similarity_threshold: number
  }
  llm: {
    provider: string
    model: string
  }
  embedding: {
    provider: string
    model: string
    dimension: number
  }
  settings: {
    include_sources: boolean
    max_context_length: number
    stream_response: boolean
  }
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query/info`)
  return handleResponse(response)
}

// ============================================================================
// Phase 2: Authentication API
// ============================================================================

let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
  if (token) {
    localStorage.setItem('auth_token', token)
  } else {
    localStorage.removeItem('auth_token')
  }
}

export function getAuthToken(): string | null {
  if (!authToken && typeof window !== 'undefined') {
    authToken = localStorage.getItem('auth_token')
  }
  return authToken
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const token = getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return headers
}

export async function signup(data: SignupRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  const result = await handleResponse<AuthResponse>(response)
  setAuthToken(result.access_token)
  return result
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  const result = await handleResponse<AuthResponse>(response)
  setAuthToken(result.access_token)
  return result
}

export async function logout(): Promise<void> {
  try {
    const token = getAuthToken()
    if (token) {
      await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
    }
  } finally {
    setAuthToken(null)
  }
}

export async function getCurrentUser(): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    headers: {
      Authorization: `Bearer ${getAuthToken()}`,
    },
  })

  return handleResponse<User>(response)
}

export async function refreshToken(refreshToken: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  const result = await handleResponse<AuthResponse>(response)
  setAuthToken(result.access_token)
  return result
}

// ============================================================================
// Phase 2: Job Tracking API
// ============================================================================

export async function listJobs(status?: string): Promise<JobListResponse> {
  const params = new URLSearchParams()
  if (status) {
    params.append('status', status)
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/jobs/?${params.toString()}`,
    {
      headers: getAuthHeaders(),
    }
  )

  return handleResponse<JobListResponse>(response)
}

export async function getJob(jobId: string): Promise<ProcessingJob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
    headers: getAuthHeaders(),
  })

  return handleResponse<ProcessingJob>(response)
}

export async function cancelJob(jobId: string): Promise<ProcessingJob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })

  return handleResponse<ProcessingJob>(response)
}

// ============================================================================
// Phase 2: Update existing functions to support authentication
// ============================================================================

export async function uploadDocumentAuthenticated(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const headers: Record<string, string> = {}
  const token = getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    method: 'POST',
    headers,
    body: formData,
  })

  return handleResponse(response)
}

export async function uploadAndProcessDocumentAuthenticated(
  file: File,
): Promise<DocumentProcessingResult> {
  const formData = new FormData()
  formData.append('file', file)

  const headers: Record<string, string> = {}
  const token = getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload-and-process`, {
    method: 'POST',
    headers,
    body: formData,
  })

  return handleResponse(response)
}

export async function listDocumentsAuthenticated(): Promise<{ documents: Document[]; total: number }> {
  const headers: Record<string, string> = {}
  const token = getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/documents/`, {
    headers,
  })
  return handleResponse(response)
}

export async function queryDocumentsAuthenticated(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })

  return handleResponse(response)
}

// ============================================================================
// Export APIError for error handling
// ============================================================================

export { APIError }
