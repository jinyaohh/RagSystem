-- ============================================================================
-- Phase 3: Analytics Schema
-- ============================================================================
-- This schema extends Phase 2 to add comprehensive analytics capabilities

-- ============================================================================
-- Query Logs Table
-- ============================================================================
-- Track all user queries for analytics and insights

CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    question TEXT NOT NULL,
    answer_length INTEGER,
    response_time_ms INTEGER NOT NULL,
    num_sources INTEGER DEFAULT 0,
    document_ids UUID[],
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    error_message TEXT,
    tokens_used INTEGER,
    model TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_status ON query_logs(status);
CREATE INDEX IF NOT EXISTS idx_query_logs_user_created ON query_logs(user_id, created_at DESC);

-- RLS Policies
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own query logs"
    ON query_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own query logs"
    ON query_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- System Metrics Table
-- ============================================================================
-- Track system-level performance metrics

CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type TEXT NOT NULL CHECK (metric_type IN (
        'api_latency',
        'error_rate',
        'throughput',
        'queue_length',
        'worker_count',
        'storage_usage',
        'active_users'
    )),
    metric_value NUMERIC NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded ON system_metrics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_type_recorded ON system_metrics(metric_type, recorded_at DESC);

-- Note: No RLS - system metrics are admin-only via API authorization

-- ============================================================================
-- Processing Analytics Table
-- ============================================================================
-- Track detailed processing performance by step

CREATE TABLE IF NOT EXISTS processing_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    processing_job_id UUID REFERENCES processing_jobs(id) ON DELETE CASCADE,
    step TEXT NOT NULL CHECK (step IN (
        'extraction',
        'chunking',
        'embedding',
        'storage'
    )),
    duration_ms INTEGER NOT NULL,
    tokens_used INTEGER,
    chunks_created INTEGER,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_processing_analytics_doc_id ON processing_analytics(document_id);
CREATE INDEX IF NOT EXISTS idx_processing_analytics_job_id ON processing_analytics(processing_job_id);
CREATE INDEX IF NOT EXISTS idx_processing_analytics_step ON processing_analytics(step);
CREATE INDEX IF NOT EXISTS idx_processing_analytics_created ON processing_analytics(created_at DESC);

-- RLS Policies - users can view analytics for their own documents
ALTER TABLE processing_analytics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own processing analytics"
    ON processing_analytics FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = processing_analytics.document_id
            AND documents.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert processing analytics for their documents"
    ON processing_analytics FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = processing_analytics.document_id
            AND documents.user_id = auth.uid()
        )
    );

-- ============================================================================
-- Enhanced User Stats Table
-- ============================================================================
-- Add new columns to existing user_stats table

ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_queries INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS avg_query_time_ms NUMERIC DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS last_query_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_failed_uploads INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_successful_queries INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_failed_queries INTEGER DEFAULT 0;

-- ============================================================================
-- Triggers for Auto-updating Stats
-- ============================================================================

-- Function to update user stats on query
CREATE OR REPLACE FUNCTION update_user_query_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_stats (
        user_id,
        total_queries,
        total_successful_queries,
        total_failed_queries,
        avg_query_time_ms,
        last_query_at
    )
    VALUES (
        NEW.user_id,
        1,
        CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
        CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
        NEW.response_time_ms,
        NEW.created_at
    )
    ON CONFLICT (user_id) DO UPDATE
    SET
        total_queries = user_stats.total_queries + 1,
        total_successful_queries = user_stats.total_successful_queries +
            CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
        total_failed_queries = user_stats.total_failed_queries +
            CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
        avg_query_time_ms = (
            (user_stats.avg_query_time_ms * user_stats.total_queries + NEW.response_time_ms) /
            (user_stats.total_queries + 1)
        ),
        last_query_at = NEW.created_at,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on query logs
DROP TRIGGER IF EXISTS trigger_update_user_query_stats ON query_logs;
CREATE TRIGGER trigger_update_user_query_stats
    AFTER INSERT ON query_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_user_query_stats();

-- ============================================================================
-- Analytics Views for Common Queries
-- ============================================================================

-- User activity summary (last 30 days)
CREATE OR REPLACE VIEW user_activity_30d AS
SELECT
    user_id,
    COUNT(*) as total_queries,
    COUNT(*) FILTER (WHERE status = 'success') as successful_queries,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_queries,
    AVG(response_time_ms) as avg_response_time_ms,
    COUNT(DISTINCT DATE(created_at)) as active_days
FROM query_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_id;

-- Document query frequency
CREATE OR REPLACE VIEW document_query_frequency AS
SELECT
    unnest(document_ids) as document_id,
    COUNT(*) as query_count,
    AVG(response_time_ms) as avg_response_time_ms,
    MAX(created_at) as last_queried_at
FROM query_logs
WHERE document_ids IS NOT NULL
GROUP BY document_id;

-- Processing performance by step
CREATE OR REPLACE VIEW processing_performance_by_step AS
SELECT
    step,
    COUNT(*) as total_runs,
    AVG(duration_ms) as avg_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as p50_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99_duration_ms,
    COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*) as success_rate_percent
FROM processing_analytics
GROUP BY step;

-- Daily system activity
CREATE OR REPLACE VIEW daily_system_activity AS
SELECT
    DATE(created_at) as activity_date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_queries,
    AVG(response_time_ms) as avg_response_time_ms,
    COUNT(*) FILTER (WHERE status = 'success') as successful_queries,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_queries
FROM query_logs
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE(created_at)
ORDER BY activity_date DESC;

-- ============================================================================
-- Functions for Analytics Queries
-- ============================================================================

-- Get user analytics for a specific period
CREATE OR REPLACE FUNCTION get_user_analytics(
    p_user_id UUID,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_documents BIGINT,
    total_queries BIGINT,
    successful_queries BIGINT,
    failed_queries BIGINT,
    avg_response_time_ms NUMERIC,
    total_storage_bytes BIGINT,
    most_queried_doc_id UUID,
    most_queried_doc_name TEXT,
    most_queried_doc_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH user_docs AS (
        SELECT COUNT(*) as doc_count, COALESCE(SUM(file_size), 0) as storage
        FROM documents
        WHERE user_id = p_user_id
    ),
    user_queries AS (
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'success') as success,
            COUNT(*) FILTER (WHERE status = 'failed') as failed,
            AVG(response_time_ms) as avg_time
        FROM query_logs
        WHERE user_id = p_user_id
        AND created_at >= NOW() - (p_days || ' days')::INTERVAL
    ),
    most_queried AS (
        SELECT
            unnest(document_ids) as doc_id,
            COUNT(*) as count
        FROM query_logs
        WHERE user_id = p_user_id
        AND document_ids IS NOT NULL
        AND created_at >= NOW() - (p_days || ' days')::INTERVAL
        GROUP BY doc_id
        ORDER BY count DESC
        LIMIT 1
    )
    SELECT
        ud.doc_count,
        COALESCE(uq.total, 0),
        COALESCE(uq.success, 0),
        COALESCE(uq.failed, 0),
        COALESCE(uq.avg_time, 0),
        ud.storage,
        mq.doc_id,
        d.filename,
        mq.count
    FROM user_docs ud
    CROSS JOIN user_queries uq
    LEFT JOIN most_queried mq ON true
    LEFT JOIN documents d ON d.id = mq.doc_id;
END;
$$ LANGUAGE plpgsql;

-- Get system overview analytics
CREATE OR REPLACE FUNCTION get_system_overview()
RETURNS TABLE (
    total_users BIGINT,
    active_users_30d BIGINT,
    total_documents BIGINT,
    total_queries BIGINT,
    total_storage_bytes BIGINT,
    avg_query_latency_ms NUMERIC,
    success_rate_percent NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM auth.users),
        (SELECT COUNT(DISTINCT user_id) FROM query_logs WHERE created_at >= NOW() - INTERVAL '30 days'),
        (SELECT COUNT(*) FROM documents),
        (SELECT COUNT(*) FROM query_logs),
        (SELECT COALESCE(SUM(file_size), 0) FROM documents),
        (SELECT AVG(response_time_ms) FROM query_logs WHERE created_at >= NOW() - INTERVAL '30 days'),
        (SELECT COUNT(*) FILTER (WHERE status = 'success') * 100.0 / NULLIF(COUNT(*), 0)
         FROM query_logs WHERE created_at >= NOW() - INTERVAL '30 days');
END;
$$ LANGUAGE plpgsql;

-- Get daily activity for user
CREATE OR REPLACE FUNCTION get_user_daily_activity(
    p_user_id UUID,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    activity_date DATE,
    query_count BIGINT,
    upload_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH date_series AS (
        SELECT generate_series(
            CURRENT_DATE - (p_days || ' days')::INTERVAL,
            CURRENT_DATE,
            '1 day'::INTERVAL
        )::DATE as d
    ),
    queries AS (
        SELECT DATE(created_at) as d, COUNT(*) as count
        FROM query_logs
        WHERE user_id = p_user_id
        AND created_at >= NOW() - (p_days || ' days')::INTERVAL
        GROUP BY DATE(created_at)
    ),
    uploads AS (
        SELECT DATE(created_at) as d, COUNT(*) as count
        FROM documents
        WHERE user_id = p_user_id
        AND created_at >= NOW() - (p_days || ' days')::INTERVAL
        GROUP BY DATE(created_at)
    )
    SELECT
        ds.d,
        COALESCE(q.count, 0),
        COALESCE(u.count, 0)
    FROM date_series ds
    LEFT JOIN queries q ON q.d = ds.d
    LEFT JOIN uploads u ON u.d = ds.d
    ORDER BY ds.d;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE query_logs IS 'Logs all user queries for analytics and insights';
COMMENT ON TABLE system_metrics IS 'System-level performance metrics';
COMMENT ON TABLE processing_analytics IS 'Detailed processing performance by step';
COMMENT ON VIEW user_activity_30d IS 'User activity summary for the last 30 days';
COMMENT ON VIEW document_query_frequency IS 'How often each document is queried';
COMMENT ON VIEW processing_performance_by_step IS 'Processing performance statistics by step';
COMMENT ON VIEW daily_system_activity IS 'Daily system activity metrics';
COMMENT ON FUNCTION get_user_analytics IS 'Get comprehensive analytics for a specific user';
COMMENT ON FUNCTION get_system_overview IS 'Get system-wide overview statistics';
COMMENT ON FUNCTION get_user_daily_activity IS 'Get daily activity breakdown for a user';
