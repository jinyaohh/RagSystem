# Phase 3 Setup Guide

This guide explains how to set up and use the Phase 3 features of the Financial RAG System, including advanced analytics, query logging, and performance monitoring.

## Overview

Phase 3 adds comprehensive analytics and insights on top of the multi-user system from Phase 2:

- **User Analytics**: Track individual usage patterns, document statistics, and query history
- **Query Logging**: Automatic logging of all queries with response times and metadata
- **Activity Tracking**: Daily breakdowns of queries and uploads over time
- **Popular Queries**: Identify frequently asked questions and their performance
- **Document Insights**: Analyze which documents are queried most often
- **System Metrics**: Monitor overall system health and performance (admin view)
- **Interactive Dashboard**: Real-time charts and visualizations with auto-refresh
- **Performance Analytics**: Track processing times by step and document type

## Prerequisites

- **Phase 2 must be completed** - Authentication and async processing are required
- Python 3.11+
- Node.js 18+
- Supabase project with Phase 2 schema already deployed
- All Phase 2 environment variables configured

## Phase 3 vs Phase 2

| Feature | Phase 2 | Phase 3 |
|---------|---------|---------|
| Analytics | No | Comprehensive analytics dashboard |
| Query Logging | No | Automatic with detailed metrics |
| Activity Tracking | No | Daily queries/uploads over time |
| Popular Queries | No | Frequency and performance analysis |
| Document Insights | Basic list | Usage analytics and query counts |
| System Overview | No | System-wide metrics (admin) |
| Charts/Graphs | No | Interactive Recharts visualizations |
| Auto-refresh | No | 30-second polling option |

## Architecture

```
┌─────────────────────────────────────┐
│  Next.js UI + Analytics Dashboard   │  Interactive charts with Recharts
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  FastAPI + Analytics Routes         │  Auto-logging middleware
└────────────────┬────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│ Query   │  │ System  │  │ Processing   │
│ Logs    │  │ Metrics │  │ Analytics    │
└─────────┘  └─────────┘  └──────────────┘
     │            │              │
     └────────────┴──────────────┘
                  ▼
        ┌──────────────────┐
        │  Supabase Views  │  Pre-aggregated queries
        │  & Functions     │  for performance
        └──────────────────┘
```

## Backend Setup

### 1. Deploy Analytics Schema

Execute the analytics schema in Supabase SQL Editor:

```bash
# View the analytics schema
cat backend/supabase_analytics_schema.sql
```

Copy and paste the entire content into Supabase SQL Editor and run it.

This creates:

**Tables:**
- `query_logs` - Log all user queries with response times, tokens, and status
- `system_metrics` - Track system-wide metrics (latency, throughput, errors)
- `processing_analytics` - Document processing performance by step and type

**Views:**
- `user_activity_30d` - Recent user activity aggregations
- `processing_performance_by_step` - Average times per processing step
- `query_stats_by_user` - Per-user query statistics

**Functions:**
- `get_user_analytics(user_id, days)` - User statistics
- `get_user_daily_activity(user_id, days)` - Daily activity breakdown
- `get_system_overview()` - System-wide overview

**Triggers:**
- `update_user_query_stats()` - Auto-update user stats on query
- `update_user_upload_stats()` - Auto-update user stats on upload

**RLS Policies:**
- Users can only view their own query logs
- Processing analytics available to document owners
- System metrics admin-only (future)

### 2. Enable Analytics in Backend

The analytics routes are automatically enabled when `AUTH_ENABLED=True` in your backend `.env` file:

```bash
# Backend .env (should already be set from Phase 2)
AUTH_ENABLED=True

# Analytics is conditionally enabled based on this flag
# No additional environment variables needed
```

### 3. Verify Analytics Service

The analytics service is automatically integrated into:

**Query Routes (`backend/app/api/routes/query.py`):**
- All queries are automatically logged to `query_logs` table
- Logs success/failure, response time, tokens used, sources
- Only logs for authenticated users
- Graceful degradation if logging fails

**Analytics Routes (`backend/app/api/routes/analytics.py`):**
- `GET /api/v1/analytics/user/stats?days=30` - User statistics
- `GET /api/v1/analytics/user/activity?period=30d` - Daily activity
- `GET /api/v1/analytics/user/popular-queries?limit=10` - Popular queries
- `GET /api/v1/analytics/system/overview` - System overview (admin)
- `GET /api/v1/analytics/documents/processing-stats` - Processing metrics
- `GET /api/v1/analytics/health` - Health check

### 4. Test Analytics Backend

Start the backend and test the health endpoint:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Test analytics health
curl http://localhost:8000/api/v1/analytics/health
```

Expected response:
```json
{
  "status": "healthy",
  "tables": ["query_logs", "system_metrics", "processing_analytics"]
}
```

## Frontend Setup

### 1. Install Dependencies

The required packages are already in `package.json`:

```bash
cd frontend
npm install
```

This installs:
- `recharts` - Chart library for visualizations
- `date-fns` - Date formatting utilities

### 2. Analytics Dashboard

The analytics dashboard is available at `/analytics` route:

**Features:**
- 4 summary cards (documents, queries, avg time, success rate)
- Activity line chart (queries and uploads over time)
- Documents by type pie chart
- Most queried documents bar chart
- Popular queries list with metrics
- Period selector (7d, 30d, 90d)
- Manual refresh button
- Auto-refresh toggle (30-second polling)
- Last updated timestamp

**Access:**
- Only available to authenticated users
- Link appears in navigation after login
- Automatically fetches user-specific data

### 3. Test Analytics Frontend

Start the frontend:

```bash
cd frontend
npm run dev
```

1. Navigate to http://localhost:3000
2. Log in with your credentials
3. Click "Analytics" in the navigation
4. You should see the analytics dashboard

**Note:** Initial data may be empty until you:
- Upload some documents
- Ask some queries via the chat interface

## Usage Guide

### Viewing Your Analytics

1. **Navigate to Analytics:**
   - Click "Analytics" link in the top navigation
   - Available only when logged in

2. **Understand the Stats Cards:**
   - **Total Documents**: Number of documents you've uploaded
   - **Total Queries**: All queries you've made (successful + failed)
   - **Avg Response Time**: Average query response time in seconds
   - **Success Rate**: Percentage of successful queries

3. **Activity Over Time Chart:**
   - Shows daily queries (blue line) and uploads (green line)
   - Helps identify usage patterns
   - Use period selector to change timeframe (7d, 30d, 90d)

4. **Documents by Type:**
   - Pie chart showing breakdown of PDF, DOCX, XLSX, TXT files
   - Only shows document types you've uploaded

5. **Most Queried Documents:**
   - Bar chart of documents you ask about most frequently
   - Helps identify your most important documents

6. **Popular Questions:**
   - List of your most frequently asked questions
   - Shows how many times asked and average response time
   - Useful for understanding common queries

### Auto-Refresh

The dashboard can automatically refresh data:

1. **Enable Auto-Refresh:**
   - Check the "Auto-refresh (30s)" checkbox in the header
   - Dashboard will fetch new data every 30 seconds
   - Last updated time is shown below the title

2. **Disable Auto-Refresh:**
   - Uncheck the checkbox to stop automatic updates
   - Use manual "Refresh" button to update on demand

### Querying Analytics Data

All analytics are automatically collected. Simply use the system normally:

1. **Upload Documents:**
   - Each upload is tracked in your stats
   - Document count and storage usage updated

2. **Ask Questions:**
   - Every query is automatically logged
   - Response time, sources, and tokens tracked
   - Success/failure status recorded

3. **View Results:**
   - Analytics dashboard shows aggregated insights
   - Data is user-specific (you only see your own analytics)

## Analytics Data Model

### Query Logs

Each query creates a record with:
- `question` - The question asked
- `answer_length` - Length of the answer in characters
- `response_time_ms` - Total response time in milliseconds
- `num_sources` - Number of source chunks used
- `document_ids` - Which documents were queried
- `status` - success or failed
- `error_message` - Error details if failed
- `tokens_used` - Number of LLM tokens consumed
- `model` - Which LLM model was used
- `created_at` - Timestamp of the query

### User Analytics Stats

Aggregated statistics include:
- Total documents and storage usage
- Total queries (successful and failed)
- Average query response time
- Documents breakdown by type
- Most queried documents with counts
- Queries in last 30 days

### Daily Activity

Daily breakdowns show:
- Date of activity
- Number of queries on that day
- Number of uploads on that day

### Popular Queries

Frequently asked questions with:
- Question text
- Number of times asked
- Average response time

## API Reference

### User Analytics Endpoints

#### Get User Stats
```bash
GET /api/v1/analytics/user/stats?days=30
Authorization: Bearer <jwt_token>
```

Returns user statistics for the last N days.

#### Get User Activity
```bash
GET /api/v1/analytics/user/activity?period=30d
Authorization: Bearer <jwt_token>
```

Returns daily breakdown of queries and uploads.
Periods: `7d`, `30d`, `90d`, `1y`

#### Get Popular Queries
```bash
GET /api/v1/analytics/user/popular-queries?limit=10
Authorization: Bearer <jwt_token>
```

Returns most frequently asked questions.

### System Analytics Endpoints

#### Get System Overview
```bash
GET /api/v1/analytics/system/overview
Authorization: Bearer <jwt_token>
```

Returns system-wide statistics.
**Note:** Currently available to all users; should be restricted to admins in production.

#### Get Processing Stats
```bash
GET /api/v1/analytics/documents/processing-stats
Authorization: Bearer <jwt_token>
```

Returns document processing performance metrics by step and type.

### Health Check
```bash
GET /api/v1/analytics/health
```

Check analytics service health. No authentication required.

## Troubleshooting

### Analytics Dashboard Shows No Data

**Cause:** No queries have been made yet, or analytics schema not deployed.

**Solution:**
1. Ensure Phase 3 schema is deployed to Supabase
2. Upload documents and ask queries via chat
3. Wait for data to populate (may take a few seconds)
4. Click "Refresh" button on dashboard

### Query Logging Not Working

**Cause:** `AUTH_ENABLED` is set to `False` or user is not authenticated.

**Solution:**
1. Check `backend/.env` has `AUTH_ENABLED=True`
2. Ensure you're logged in when making queries
3. Check backend logs for analytics logging errors
4. Verify Supabase connection is working

### "Analytics require authentication to be enabled" Error

**Cause:** Trying to access analytics with `AUTH_ENABLED=False`.

**Solution:**
Analytics is only available when authentication is enabled. Set `AUTH_ENABLED=True` in backend `.env` and restart the server.

### Auto-Refresh Not Working

**Cause:** Browser tab is inactive or checkbox is unchecked.

**Solution:**
1. Ensure "Auto-refresh (30s)" checkbox is checked
2. Keep browser tab active (some browsers pause timers on inactive tabs)
3. Check browser console for errors

### Database Function Errors

**Cause:** Analytics schema functions not created or have errors.

**Solution:**
1. Re-run `backend/supabase_analytics_schema.sql` in Supabase SQL Editor
2. Check for SQL errors in the execution
3. Verify functions exist in Supabase Database → Functions

## Performance Considerations

### Query Logging Overhead

- Query logging is asynchronous and doesn't block requests
- Failed logging attempts don't affect query responses
- Minimal performance impact (< 5ms per query)

### Dashboard Performance

- Analytics queries use database views for efficiency
- Pre-aggregated data reduces computation
- Auto-refresh uses client-side polling (no server overhead)
- Indexes on `query_logs` ensure fast queries

### Data Retention

Currently, all analytics data is retained indefinitely. For production systems, consider:

1. **Archiving Old Data:**
   ```sql
   -- Archive query logs older than 1 year
   DELETE FROM query_logs WHERE created_at < NOW() - INTERVAL '1 year';
   ```

2. **Partitioning Tables:**
   - Partition `query_logs` by month for better performance
   - Use PostgreSQL table partitioning features

3. **Data Aggregation:**
   - Store daily aggregates instead of individual queries
   - Reduce storage requirements

## Security Considerations

### Row Level Security (RLS)

All analytics tables have RLS policies:
- Users can only query their own `query_logs`
- `processing_analytics` tied to document ownership
- `system_metrics` should be admin-only (to be implemented)

### Data Privacy

- Query logs contain user questions (may be sensitive)
- Ensure GDPR compliance if storing user data
- Provide data export and deletion mechanisms

### Admin Access

System overview and processing stats are currently available to all authenticated users. For production:

1. Add admin role to users table
2. Update RLS policies to restrict access
3. Add admin role check in analytics routes

## Next Steps

After completing Phase 3:

1. **Add Unit Tests:**
   - Test analytics service methods
   - Test API endpoints
   - Test dashboard components

2. **Implement Admin Dashboard:**
   - System-wide metrics and insights
   - User management
   - Processing queue monitoring

3. **Add Export Functionality:**
   - Export analytics data as CSV/Excel
   - Generate PDF reports
   - Email periodic analytics summaries

4. **Optimize Performance:**
   - Add database indexes
   - Implement caching
   - Use database materialized views

5. **Enhance Visualizations:**
   - Add more chart types
   - Implement drill-down capabilities
   - Add comparison views

## Support

For issues or questions:
- Check the troubleshooting section above
- Review backend logs for detailed error messages
- Verify Supabase SQL functions are created correctly
- Ensure Phase 2 is fully operational before troubleshooting Phase 3

## Resources

- [Recharts Documentation](https://recharts.org/)
- [Supabase Database Functions](https://supabase.com/docs/guides/database/functions)
- [PostgreSQL Aggregation](https://www.postgresql.org/docs/current/functions-aggregate.html)
- Phase 3 Implementation Plan: `PHASE3_IMPLEMENTATION_PLAN.md`
- Phase 2 Setup Guide: `PHASE2_SETUP.md`
