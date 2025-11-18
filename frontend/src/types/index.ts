// API Response Types

export interface DocumentUploadResponse {
  document_id: string
  filename: string
  file_type: string
  file_size: number
  status: string
  message: string
}

export interface DocumentProcessingResult {
  document_id: string
  filename: string
  file_type: string
  status: string
  extraction?: {
    text_length: number
    metadata: Record<string, any>
  }
  chunking?: {
    num_chunks: number
    avg_chunk_size: number
  }
  embedding?: {
    model: string
    dimension: number
    tokens_used: number
  }
  storage?: {
    num_stored: number
    collection: string
    chunk_ids: string[]
  }
  error?: string
  message?: string
}

export interface Document {
  document_id: string
  filename: string
  file_type: string
  file_size: number
  upload_date: number
}

export interface QueryRequest {
  question: string
  top_k?: number
  include_sources?: boolean
  document_ids?: string[]
}

export interface QueryResponse {
  question: string
  answer: string
  status: string
  response_time_ms: number
  retrieval_stats?: {
    num_results: number
    avg_score: number
    min_score: number
    max_score: number
  }
  llm_stats?: {
    model: string
    tokens_used: number
    finish_reason: string
  }
  sources?: Array<{
    filename: string
    page: string
    score: string
    preview: string
  }>
  num_sources?: number
  error?: string
}

export interface HealthResponse {
  status: string
  app_name: string
  version: string
  environment: string
  services?: {
    llm: {
      provider: string
      model: string
      status: string
    }
    embedding: {
      provider: string
      model: string
      dimension: number
      status: string
    }
    vector_db: {
      type: string
      host: string
      port: number
      status: string
    }
    collection: {
      name: string
      exists: boolean
      vectors_count?: number
      points_count?: number
    }
  }
  config?: {
    chunk_size: number
    chunk_overlap: number
    top_k: number
    max_file_size: number
  }
}

// UI State Types

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: QueryResponse['sources']
  timestamp: Date
  status?: 'sending' | 'sent' | 'error'
}

export interface UploadState {
  file: File | null
  uploading: boolean
  progress: number
  result: DocumentProcessingResult | null
  error: string | null
}

// ============================================================================
// Phase 2: Authentication & Job Tracking Types
// ============================================================================

export interface User {
  id: string
  email: string
  full_name?: string
  created_at: string
  total_documents?: number
  total_queries?: number
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
  expires_in: number
}

export interface SignupRequest {
  email: string
  password: string
  full_name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export enum JobStatus {
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum ProcessingStep {
  QUEUED = 'queued',
  EXTRACTION = 'extraction',
  CHUNKING = 'chunking',
  EMBEDDING = 'embedding',
  STORAGE = 'storage',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface ProcessingJob {
  id: string
  document_id: string
  user_id: string
  status: JobStatus
  task_id: string
  progress: number
  current_step?: ProcessingStep
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface JobListResponse {
  jobs: ProcessingJob[]
  total: number
  status_counts: Record<JobStatus, number>
}

// ============================================================================
// Phase 3: Analytics Types
// ============================================================================

export interface DocumentTypeStats {
  pdf: number
  docx: number
  xlsx: number
  txt: number
}

export interface MostQueriedDocument {
  document_id: string
  filename: string
  query_count: number
}

export interface UserAnalyticsStats {
  total_documents: number
  total_queries: number
  successful_queries: number
  failed_queries: number
  total_storage_bytes: number
  avg_query_time_ms: number
  documents_by_type: DocumentTypeStats
  queries_last_30_days: number
  most_queried_documents: MostQueriedDocument[]
}

export interface DailyActivity {
  date: string
  count: number
}

export interface UserActivityResponse {
  period: string
  daily_queries: DailyActivity[]
  daily_uploads: DailyActivity[]
}

export interface PopularQuery {
  question: string
  count: number
  avg_response_time_ms: number
}

export interface PopularQueriesResponse {
  queries: PopularQuery[]
}

export interface SystemOverview {
  total_users: number
  active_users_30d: number
  total_documents: number
  total_queries: number
  total_storage_gb: number
  avg_query_latency_ms: number
  success_rate_percent: number
  processing_queue_length: number
}

export interface StepPerformance {
  avg_ms: number
  min_ms: number
  max_ms: number
  p50_ms: number
  p95_ms: number
  p99_ms: number
  success_rate: number
}

export interface TypePerformance {
  avg_ms: number
  count: number
}

export interface ProcessingStatsResponse {
  avg_processing_time_ms: number
  total_processed: number
  processing_by_step: Record<string, StepPerformance>
  processing_by_type: Record<string, TypePerformance>
}
