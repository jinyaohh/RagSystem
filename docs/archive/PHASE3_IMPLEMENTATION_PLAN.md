# Phase 3 Implementation Plan: Advanced Analytics Dashboard

## Overview

Phase 3 adds a comprehensive analytics dashboard that provides insights into system usage, user activity, and document processing performance. This builds on Phase 2's multi-user infrastructure.

## Goals

- **User Analytics**: Track individual user activity and usage patterns
- **System Metrics**: Monitor overall system health and performance
- **Document Insights**: Analyze document processing statistics
- **Query Analytics**: Understand what questions users are asking
- **Visual Dashboard**: Interactive charts and graphs for data visualization

## Timeline: 2 Weeks

### Week 1: Backend Analytics Infrastructure
- [ ] Database schema for analytics tables
- [ ] Analytics service layer
- [ ] Metrics collection middleware
- [ ] Analytics API endpoints
- [ ] Aggregation functions

### Week 2: Frontend Dashboard
- [ ] Dashboard layout and components
- [ ] Chart library integration (Recharts)
- [ ] User analytics view
- [ ] System metrics view
- [ ] Real-time updates

## Architecture

```
┌─────────────────────────────────────────┐
│         Frontend Dashboard              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  User   │  │ System  │  │Document │ │
│  │Analytics│  │ Metrics │  │ Insights│ │
│  └─────────┘  └─────────┘  └─────────┘ │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      Analytics API Endpoints            │
│  GET /api/v1/analytics/user             │
│  GET /api/v1/analytics/system           │
│  GET /api/v1/analytics/documents        │
│  GET /api/v1/analytics/queries          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      Analytics Service Layer            │
│  - Aggregation logic                    │
│  - Time-series data processing          │
│  - Trend calculations                   │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         Supabase Database               │
│  - query_logs table                     │
│  - user_stats table (enhanced)          │
│  - system_metrics table                 │
│  - processing_analytics table           │
└─────────────────────────────────────────┘
```

## Database Schema

### New Tables

#### query_logs
Track all queries for analytics:
```sql
CREATE TABLE query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    question TEXT NOT NULL,
    answer_length INTEGER,
    response_time_ms INTEGER,
    num_sources INTEGER,
    document_ids UUID[],
    status TEXT NOT NULL, -- 'success', 'failed'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### system_metrics
Track system-level metrics:
```sql
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type TEXT NOT NULL, -- 'api_latency', 'error_rate', 'throughput'
    metric_value NUMERIC NOT NULL,
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

#### processing_analytics
Track processing performance:
```sql
CREATE TABLE processing_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    processing_job_id UUID REFERENCES processing_jobs(id) ON DELETE CASCADE,
    step TEXT NOT NULL, -- 'extraction', 'chunking', 'embedding', 'storage'
    duration_ms INTEGER NOT NULL,
    tokens_used INTEGER,
    chunks_created INTEGER,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

### Enhanced Tables

Update `user_stats` with more fields:
```sql
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_queries INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS avg_query_time_ms NUMERIC;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS last_query_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_failed_uploads INTEGER DEFAULT 0;
```

## API Endpoints

### User Analytics
```
GET /api/v1/analytics/user/stats
Response:
{
  "total_documents": 15,
  "total_queries": 142,
  "total_storage_bytes": 52428800,
  "avg_query_time_ms": 2341,
  "documents_by_type": {
    "pdf": 10,
    "docx": 3,
    "xlsx": 2
  },
  "queries_last_30_days": 45,
  "most_queried_documents": [
    {"document_id": "...", "filename": "Q4-report.pdf", "query_count": 23}
  ]
}

GET /api/v1/analytics/user/activity
Query params: ?period=7d|30d|90d|1y
Response:
{
  "period": "30d",
  "daily_queries": [
    {"date": "2024-01-01", "count": 5},
    {"date": "2024-01-02", "count": 8}
  ],
  "daily_uploads": [
    {"date": "2024-01-01", "count": 2},
    {"date": "2024-01-02", "count": 1}
  ]
}

GET /api/v1/analytics/user/popular-queries
Response:
{
  "queries": [
    {"question": "What was the revenue?", "count": 12, "avg_response_time_ms": 2100},
    {"question": "Compare profit margins", "count": 8, "avg_response_time_ms": 2400}
  ]
}
```

### System Analytics (Admin Only)
```
GET /api/v1/analytics/system/overview
Response:
{
  "total_users": 127,
  "active_users_30d": 89,
  "total_documents": 1453,
  "total_queries": 5621,
  "total_storage_gb": 12.4,
  "avg_query_latency_ms": 2234,
  "error_rate_percent": 1.2,
  "processing_queue_length": 3
}

GET /api/v1/analytics/system/performance
Query params: ?period=1h|24h|7d|30d
Response:
{
  "period": "24h",
  "api_latency_p50": 1200,
  "api_latency_p95": 3500,
  "api_latency_p99": 5200,
  "throughput_rpm": 45,
  "error_rate": 0.8,
  "active_celery_workers": 3
}

GET /api/v1/analytics/system/usage-trends
Response:
{
  "user_growth": [
    {"month": "2024-01", "new_users": 23, "total_users": 89}
  ],
  "document_growth": [
    {"month": "2024-01", "new_documents": 234, "total_documents": 1200}
  ],
  "query_volume": [
    {"month": "2024-01", "queries": 1234}
  ]
}
```

### Document Analytics
```
GET /api/v1/analytics/documents/processing-stats
Response:
{
  "avg_processing_time_ms": 45000,
  "processing_by_step": {
    "extraction": {"avg_ms": 12000, "success_rate": 98.5},
    "chunking": {"avg_ms": 8000, "success_rate": 99.8},
    "embedding": {"avg_ms": 20000, "success_rate": 99.2},
    "storage": {"avg_ms": 5000, "success_rate": 100}
  },
  "processing_by_type": {
    "pdf": {"avg_ms": 50000, "count": 850},
    "docx": {"avg_ms": 35000, "count": 420}
  }
}
```

## Frontend Components

### Dashboard Layout
```
┌─────────────────────────────────────────────────────┐
│  Analytics Dashboard                    [Filter: 30d]│
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │Documents │  │ Queries  │  │  Avg     │          │
│  │   142    │  │   1,234  │  │Response  │          │
│  │  +12%    │  │  +23%    │  │  2.3s    │          │
│  └──────────┘  └──────────┘  └──────────┘          │
├─────────────────────────────────────────────────────┤
│  Query Activity (Last 30 Days)                      │
│  ┌─────────────────────────────────────────────┐   │
│  │         Line Chart: Queries Over Time       │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐│
│  │ Documents by Type    │  │ Most Queried Docs    ││
│  │  Pie Chart           │  │  Bar Chart           ││
│  │                      │  │                      ││
│  └──────────────────────┘  └──────────────────────┘│
├─────────────────────────────────────────────────────┤
│  Popular Questions                                  │
│  1. "What was the revenue?" - 23 times             │
│  2. "Compare profit margins" - 18 times            │
│  3. "List risk factors" - 12 times                 │
└─────────────────────────────────────────────────────┘
```

### Component Tree
```
/analytics
├── AnalyticsDashboard (page.tsx)
│   ├── StatsCards
│   │   ├── StatCard (documents)
│   │   ├── StatCard (queries)
│   │   └── StatCard (avg response time)
│   ├── ActivityChart
│   │   └── LineChart (queries over time)
│   ├── DocumentsChart
│   │   └── PieChart (by type)
│   ├── PopularDocsChart
│   │   └── BarChart (most queried)
│   └── PopularQueries
│       └── List (top questions)
└── components/
    ├── StatCard.tsx
    ├── ActivityChart.tsx
    ├── DocumentsChart.tsx
    ├── PopularDocsChart.tsx
    └── PopularQueries.tsx
```

## Chart Library: Recharts

Install dependencies:
```bash
npm install recharts
npm install @types/recharts --save-dev
```

## Middleware for Metrics Collection

Create middleware to automatically log queries and track metrics:

```python
# backend/app/middleware/analytics.py
@app.middleware("http")
async def analytics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration_ms = int((time.time() - start_time) * 1000)

    # Log API metrics
    if request.url.path.startswith("/api/v1"):
        await log_api_metric(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms
        )

    return response
```

## Real-time Updates

Use polling or WebSockets for real-time dashboard updates:

```typescript
// Option 1: Polling every 30 seconds
useEffect(() => {
  const interval = setInterval(() => {
    fetchAnalytics()
  }, 30000)

  return () => clearInterval(interval)
}, [])

// Option 2: WebSocket (future enhancement)
const ws = new WebSocket('ws://localhost:8000/ws/analytics')
ws.onmessage = (event) => {
  updateMetrics(JSON.parse(event.data))
}
```

## Security

- User analytics: Only show user's own data
- System analytics: Require admin role
- RLS policies: Ensure users can only see their query logs
- Rate limiting: Prevent excessive analytics queries

## Success Metrics

- Dashboard loads in < 2 seconds
- Charts render smoothly (60fps)
- Real-time updates without performance impact
- Users can identify usage patterns
- Admins can monitor system health

## Implementation Steps

### Backend (Week 1)
1. Create analytics database schema
2. Add analytics service layer
3. Implement metrics collection middleware
4. Create analytics API endpoints
5. Add aggregation queries
6. Write unit tests

### Frontend (Week 2)
1. Install Recharts library
2. Create analytics page structure
3. Build StatCard components
4. Implement activity charts
5. Add document analytics charts
6. Create popular queries list
7. Add loading and error states
8. Implement data refresh logic

## Testing

- Unit tests for analytics service
- Integration tests for API endpoints
- Frontend component tests
- E2E tests for dashboard
- Performance tests for aggregation queries

## Future Enhancements

- Export analytics to CSV/PDF
- Custom date range selection
- Scheduled email reports
- Anomaly detection alerts
- Comparative analytics (week-over-week)
- Predictive analytics (forecasting)
- Cost analytics (API usage)

## Dependencies

### Backend
- No new dependencies (use existing Supabase, FastAPI)

### Frontend
- `recharts` - Charting library
- `date-fns` - Date manipulation
- `react-loading-skeleton` - Loading states

---

**Phase 3 Status**: Ready to implement
**Estimated Completion**: 2 weeks
**Priority**: High - Provides valuable insights for users and admins
