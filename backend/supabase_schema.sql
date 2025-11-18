-- ============================================================================
-- Supabase Database Schema for Financial RAG System - Phase 2
-- ============================================================================
-- This script creates the database schema for multi-user RAG system
-- Run this in your Supabase SQL Editor

-- ============================================================================
-- Enable UUID Extension
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Documents Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT,  -- Local file path (for backward compatibility)
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path TEXT NOT NULL,  -- Supabase Storage path
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    processing_job_id UUID,  -- References processing_jobs(id)

    -- Processing metadata
    total_pages INTEGER,
    total_chunks INTEGER,
    processing_time_ms INTEGER,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_file_size CHECK (file_size > 0),
    CONSTRAINT valid_file_type CHECK (file_type IN ('pdf', 'docx', 'xlsx', 'txt', 'doc', 'xls'))
);

-- ============================================================================
-- Document Chunks Table (for reference and tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    vector_id TEXT NOT NULL,  -- Qdrant point ID
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT unique_document_chunk UNIQUE (document_id, chunk_index),
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0)
);

-- ============================================================================
-- Processing Jobs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',  -- queued, processing, completed, failed, cancelled
    task_id TEXT NOT NULL UNIQUE,  -- Celery task ID
    progress INTEGER DEFAULT 0,  -- 0-100
    current_step TEXT,  -- queued, extraction, chunking, embedding, storage, completed, failed
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_status_job CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100),
    CONSTRAINT valid_step CHECK (current_step IN ('queued', 'extraction', 'chunking', 'embedding', 'storage', 'completed', 'failed'))
);

-- ============================================================================
-- User Settings Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- User Statistics Table (for analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_stats (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    total_documents INTEGER DEFAULT 0,
    total_queries INTEGER DEFAULT 0,
    total_storage_bytes BIGINT DEFAULT 0,
    documents_by_type JSONB DEFAULT '{}',
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT valid_total_documents CHECK (total_documents >= 0),
    CONSTRAINT valid_total_queries CHECK (total_queries >= 0),
    CONSTRAINT valid_storage CHECK (total_storage_bytes >= 0)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_user_status ON documents(user_id, status);

-- Document chunks indexes
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_vector_id ON document_chunks(vector_id);

-- Processing jobs indexes
CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id ON processing_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_user_id ON processing_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_task_id ON processing_jobs(task_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_created_at ON processing_jobs(created_at DESC);

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;

-- Documents policies
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

-- Document chunks policies
CREATE POLICY "Users can view chunks from their documents"
    ON document_chunks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = document_chunks.document_id
            AND documents.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert chunks for their documents"
    ON document_chunks FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = document_chunks.document_id
            AND documents.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete chunks from their documents"
    ON document_chunks FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = document_chunks.document_id
            AND documents.user_id = auth.uid()
        )
    );

-- Processing jobs policies
CREATE POLICY "Users can view their own processing jobs"
    ON processing_jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own processing jobs"
    ON processing_jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own processing jobs"
    ON processing_jobs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own processing jobs"
    ON processing_jobs FOR DELETE
    USING (auth.uid() = user_id);

-- User settings policies
CREATE POLICY "Users can view their own settings"
    ON user_settings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own settings"
    ON user_settings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own settings"
    ON user_settings FOR UPDATE
    USING (auth.uid() = user_id);

-- User stats policies
CREATE POLICY "Users can view their own stats"
    ON user_stats FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own stats"
    ON user_stats FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own stats"
    ON user_stats FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================================================
-- Triggers for Automatic Timestamp Updates
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for documents table
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_settings table
CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_stats table
CREATE TRIGGER update_user_stats_updated_at
    BEFORE UPDATE ON user_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Functions for Statistics
-- ============================================================================

-- Function to increment user document count
CREATE OR REPLACE FUNCTION increment_user_document_count()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_stats (user_id, total_documents, total_storage_bytes, last_activity)
    VALUES (NEW.user_id, 1, NEW.file_size, NOW())
    ON CONFLICT (user_id) DO UPDATE
    SET total_documents = user_stats.total_documents + 1,
        total_storage_bytes = user_stats.total_storage_bytes + NEW.file_size,
        last_activity = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update user stats on document insert
CREATE TRIGGER update_user_stats_on_document_insert
    AFTER INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION increment_user_document_count();

-- Function to decrement user document count
CREATE OR REPLACE FUNCTION decrement_user_document_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_stats
    SET total_documents = GREATEST(0, total_documents - 1),
        total_storage_bytes = GREATEST(0, total_storage_bytes - OLD.file_size),
        last_activity = NOW()
    WHERE user_id = OLD.user_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update user stats on document delete
CREATE TRIGGER update_user_stats_on_document_delete
    AFTER DELETE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION decrement_user_document_count();

-- ============================================================================
-- Initial Data / Sample Records (Optional)
-- ============================================================================

-- You can add sample data here if needed for testing

-- ============================================================================
-- Supabase Storage Bucket Configuration
-- ============================================================================

-- NOTE: Storage buckets are created via Supabase Dashboard or Storage API
-- Bucket name: 'documents'
-- Public: false (private)
-- File size limit: 50MB
-- Allowed MIME types: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, etc.

-- Storage policies (run in Supabase Dashboard > Storage > Policies):
/*
-- Users can upload to their own folder
CREATE POLICY "Users can upload their own documents"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'documents' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can view their own documents
CREATE POLICY "Users can view their own documents"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'documents' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can delete their own documents
CREATE POLICY "Users can delete their own documents"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'documents' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );
*/

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Check policies
SELECT tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';

-- ============================================================================
-- End of Schema
-- ============================================================================
