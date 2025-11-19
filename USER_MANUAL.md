# Financial RAG System - User Manual

**Version:** 3.0 (Phase 3 - Analytics Dashboard)
**Last Updated:** November 2025

Complete guide to using the Financial Reports RAG System.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Document Management](#document-management)
4. [Asking Questions](#asking-questions)
5. [Job Tracking](#job-tracking)
6. [Analytics Dashboard](#analytics-dashboard)
7. [User Account](#user-account)
8. [Tips & Best Practices](#tips--best-practices)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Introduction

The Financial RAG System is an AI-powered platform that allows you to upload financial documents and ask questions about them in natural language. The system uses advanced retrieval-augmented generation (RAG) to provide accurate, cited answers from your documents.

### Key Features

**Document Processing:**
- Upload PDF, Word (DOCX), Excel (XLSX), and text files
- Automatic text extraction and indexing
- Background processing with progress tracking

**Intelligent Querying:**
- Ask questions in plain English
- Get AI-generated answers with source citations
- View confidence scores and supporting evidence

**Analytics & Insights:**
- Track your usage patterns
- See which documents you query most
- Monitor query performance metrics
- View activity trends over time

### System Requirements

**For Users:**
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- Valid user account (for multi-user deployments)

**Supported Document Formats:**
- PDF (.pdf) - up to 100 pages
- Microsoft Word (.docx)
- Microsoft Excel (.xlsx, .xls)
- Plain text (.txt)

---

## Getting Started

### Creating an Account

1. Navigate to the application URL (e.g., http://your-domain.com)
2. Click **"Sign Up"** in the top-right corner
3. Enter your email address
4. Create a strong password (minimum 8 characters)
5. Optionally enter your full name
6. Click **"Create Account"**
7. You'll be automatically logged in

### Logging In

1. Go to the application homepage
2. Click **"Login"**
3. Enter your email and password
4. Click **"Sign In"**

Your session will remain active for 7 days unless you log out.

### Navigation

The main navigation bar contains:
- **Home** - Dashboard and overview
- **Upload** - Upload new documents
- **Chat** - Ask questions about your documents
- **Documents** - View and manage your uploaded documents
- **Jobs** - Track document processing status (requires authentication)
- **Analytics** - View usage insights and statistics (requires authentication)

---

## Document Management

### Uploading Documents

#### Via Upload Page

1. Click **"Upload"** in the navigation
2. Click **"Choose File"** or drag-and-drop a document
3. Optionally add tags or metadata
4. Click **"Upload"**

The document will be queued for processing. You'll see:
- Upload confirmation
- Processing job ID
- Link to track progress in Jobs page

#### Processing Stages

Your document goes through four stages:

1. **Extraction** (25%) - Text is extracted from the file
2. **Chunking** (50%) - Text is split into manageable segments
3. **Embedding** (75%) - AI generates semantic vectors
4. **Storage** (100%) - Vectors are stored in the database

**Processing Times:**
- Small documents (< 10 pages): 30-60 seconds
- Medium documents (10-50 pages): 1-3 minutes
- Large documents (50+ pages): 3-10 minutes

### Viewing Documents

1. Click **"Documents"** in the navigation
2. Browse your uploaded documents
3. Each document shows:
   - Filename and type
   - Upload date
   - File size
   - Processing status
   - Number of chunks created

### Document Actions

**View Details:**
- Click on a document to see:
  - Full metadata
  - Processing history
  - Number of times queried
  - Associated queries

**Delete Document:**
1. Click the trash icon next to a document
2. Confirm deletion
3. Document and all its data will be permanently removed

⚠️ **Warning:** Deleting a document cannot be undone.

### Document Organization

**Search Documents:**
- Use the search box to find documents by name
- Filter by document type (PDF, DOCX, XLSX, TXT)
- Sort by date, name, or size

**Tags (if available):**
- Add tags to categorize documents
- Filter documents by tag
- Organize related documents together

---

## Asking Questions

### Using the Chat Interface

1. Click **"Chat"** in the navigation
2. Select which documents to query (or query all)
3. Type your question in the input box
4. Press Enter or click **"Ask"**

### Question Types

**Factual Questions:**
```
"What was the total revenue in Q4 2023?"
"Who is the CEO mentioned in the report?"
"What is the company's main product?"
```

**Analytical Questions:**
```
"What are the main risk factors identified?"
"How did profit margins change from 2022 to 2023?"
"What trends are mentioned in the market analysis?"
```

**Summarization:**
```
"Summarize the executive summary"
"What are the key findings of this report?"
"Give me an overview of the financial performance"
```

**Comparative Questions:**
```
"Compare the revenue between Q1 and Q4"
"How does this year's performance compare to last year?"
"What are the differences between Product A and Product B?"
```

### Understanding Answers

Each answer includes:

**Main Answer:**
- AI-generated response to your question
- Written in clear, concise language

**Source Citations:**
- Direct quotes or references from your documents
- Page numbers or section references
- Confidence scores for each source

**Metadata:**
- Response time
- Number of sources consulted
- Model used (e.g., GPT-4)
- Tokens consumed

### Answer Quality Indicators

**High Confidence:**
- Multiple supporting sources
- Consistent information across sources
- Direct quotes available

**Medium Confidence:**
- Limited sources
- Some ambiguity in the answer
- Indirect references

**Low Confidence:**
- Very few or no sources found
- Answer may be speculative
- Consider rephrasing your question

### Tips for Better Questions

✅ **Do:**
- Be specific and clear
- Use proper terminology from your documents
- Break complex questions into simpler parts
- Reference specific documents if relevant

❌ **Don't:**
- Ask questions requiring external knowledge
- Use overly vague or broad questions
- Expect the system to perform calculations (unless stated in the document)
- Ask about documents you haven't uploaded

---

## Job Tracking

The Jobs page shows the status of all your document processing tasks.

### Job Statuses

**Queued:**
- Job is waiting to be processed
- Position in queue shown

**Processing:**
- Job is currently running
- Progress bar shows completion percentage
- Current step displayed (extraction/chunking/embedding/storage)

**Completed:**
- Job finished successfully
- Document is ready for querying
- Shows total processing time

**Failed:**
- Job encountered an error
- Error message displayed
- Option to retry

### Job Actions

**View Details:**
- Click on a job to see:
  - Start and end times
  - Detailed progress log
  - Resource usage
  - Error details (if failed)

**Cancel Job:**
1. Click "Cancel" next to a queued or processing job
2. Confirm cancellation
3. Job will be stopped and document removed

**Retry Failed Job:**
1. Click "Retry" next to a failed job
2. Job will be re-queued
3. Previous error details preserved

### Monitoring

**Real-time Updates:**
- Job status updates automatically every 5 seconds
- No need to refresh the page
- Progress bars update in real-time

**Notifications:**
- Success notification when job completes
- Error alert if job fails
- Email notifications (if configured)

---

## Analytics Dashboard

View comprehensive insights into your usage patterns.

### Accessing Analytics

1. Click **"Analytics"** in the navigation
2. Dashboard loads with your personal analytics
3. Use the period selector to change timeframe (7d, 30d, 90d)

### Analytics Overview Cards

**Total Documents:**
- Number of documents you've uploaded
- Total storage used
- Growth compared to previous period

**Total Queries:**
- Number of questions asked
- Successful vs failed queries
- Average per day

**Average Response Time:**
- Mean time to answer queries
- Performance trend
- Comparison to baseline

**Success Rate:**
- Percentage of successful queries
- Number of failed queries
- Quality indicator

### Activity Over Time Chart

**Shows:**
- Daily query count (blue line)
- Daily upload count (green line)
- Trends over selected period

**Insights:**
- Identify your most active days
- See usage patterns
- Plan for peak usage times

### Documents by Type

**Pie Chart showing:**
- PDF documents
- Word documents (DOCX)
- Excel spreadsheets (XLSX)
- Text files (TXT)

**Use this to:**
- Understand your document mix
- Plan storage needs
- Optimize for common formats

### Most Queried Documents

**Bar chart displaying:**
- Top 10 most frequently queried documents
- Number of queries per document
- Your most valuable documents

**Insights:**
- Which documents are most important to you
- Documents that may need updating
- Reference materials you use often

### Popular Questions

**List showing:**
- Your most frequently asked questions
- Number of times each was asked
- Average response time per question

**Use this to:**
- Create quick reference guides
- Identify common information needs
- Optimize frequently accessed data

### Auto-Refresh

**Toggle auto-refresh:**
- Check "Auto-refresh (30s)" to enable
- Dashboard updates every 30 seconds
- See last updated timestamp
- Disable if you prefer manual control

---

## User Account

### Profile Settings

1. Click on your email in the top-right
2. Select **"Profile"**
3. Update your information:
   - Full name
   - Email (requires verification)
   - Password
   - Notification preferences

### Changing Password

1. Go to Profile settings
2. Click **"Change Password"**
3. Enter current password
4. Enter new password (minimum 8 characters)
5. Confirm new password
6. Click **"Update Password"**

### Usage Limits

**Free Tier:**
- 100 MB total storage
- 500 queries per month
- 10 concurrent jobs

**Pro Tier:**
- 10 GB total storage
- Unlimited queries
- 100 concurrent jobs
- Priority processing

Check your current usage in Analytics → User Stats.

### Data Export

**Export your data:**
1. Go to Profile → Data Export
2. Select what to export:
   - Documents (original files)
   - Query history
   - Analytics data
3. Choose format (ZIP, CSV, JSON)
4. Click **"Request Export"**
5. Download link sent to your email

### Account Deletion

⚠️ **This action is permanent and cannot be undone.**

1. Go to Profile → Account Settings
2. Click **"Delete Account"**
3. Enter your password
4. Type "DELETE" to confirm
5. Click **"Permanently Delete Account"**

All your documents, queries, and data will be permanently deleted.

---

## Tips & Best Practices

### Document Preparation

✅ **Best Practices:**
- Use high-quality scans for PDFs
- Ensure text is searchable (not just images)
- Remove unnecessary pages
- Use descriptive filenames
- Tag documents appropriately

### Querying Strategies

**For Best Results:**
1. **Start broad, then narrow:**
   - First: "What does this document cover?"
   - Then: "What are the specific revenue figures for Product X?"

2. **Use document terminology:**
   - If the document says "EBITDA", use that instead of "earnings"
   - Match the language and style of your documents

3. **Multi-step questioning:**
   - Break complex questions into steps
   - Build on previous answers
   - Reference specific sections

4. **Leverage sources:**
   - Check the source citations
   - Cross-reference multiple answers
   - Verify important facts

### Performance Optimization

**Faster Queries:**
- Specify which documents to search
- Use more specific questions
- Limit the number of sources requested

**Better Accuracy:**
- Upload well-structured documents
- Use clear, unambiguous questions
- Verify answers against sources

### Security Best Practices

🔒 **Protect Your Account:**
- Use a strong, unique password
- Log out on shared computers
- Don't share your credentials
- Enable two-factor authentication (if available)

🔒 **Protect Your Data:**
- Only upload documents you have rights to use
- Mark sensitive documents appropriately
- Review sharing settings before sharing
- Regularly audit your uploaded documents

---

## Troubleshooting

### Common Issues

#### "Document upload failed"

**Possible causes:**
- File too large (> 100 MB)
- Unsupported file format
- Corrupt file
- Network issues

**Solutions:**
1. Check file size and format
2. Try a different file
3. Check your internet connection
4. Contact support if issue persists

#### "No sources found for query"

**Possible causes:**
- Question not related to uploaded documents
- Documents still processing
- Poor keyword match

**Solutions:**
1. Verify documents are fully processed
2. Rephrase your question
3. Try broader search terms
4. Check that relevant documents are uploaded

#### "Query timed out"

**Possible causes:**
- Very large document set
- Complex question
- System overload

**Solutions:**
1. Narrow your search to specific documents
2. Simplify your question
3. Try again during off-peak hours

#### "Session expired"

**Cause:** You've been inactive for more than 7 days

**Solution:**
1. Log in again
2. Your documents and data are safe
3. Continue where you left off

### Performance Issues

**Slow Upload:**
- Check internet speed
- Try smaller files
- Upload during off-peak hours

**Slow Queries:**
- First query is always slower (cold start)
- Subsequent queries are faster
- Reduce number of documents searched

**Dashboard Not Loading:**
- Refresh the page
- Clear browser cache
- Check browser console for errors
- Try different browser

### Getting Help

**Self-Service:**
1. Check this manual
2. Review QUICKSTART.md
3. Check API documentation at `/docs`

**Contact Support:**
- Email: support@example.com
- GitHub Issues: Report bugs or request features
- Documentation: Browse the docs/ folder

---

## FAQ

### General

**Q: What types of documents can I upload?**
A: PDF, Word (DOCX), Excel (XLSX), and plain text (TXT) files up to 100 MB.

**Q: How many documents can I upload?**
A: Depends on your plan. Free tier: 100 MB total. Pro tier: 10 GB total.

**Q: Is my data secure?**
A: Yes. All data is encrypted in transit and at rest. See our security policy for details.

**Q: Can I share documents with others?**
A: Document sharing is planned for a future release.

### Processing

**Q: How long does processing take?**
A: Small documents (< 10 pages): 30-60 seconds. Large documents (50+ pages): 3-10 minutes.

**Q: What happens if processing fails?**
A: You'll see an error message with details. You can retry the job from the Jobs page.

**Q: Can I cancel a job?**
A: Yes, cancel queued or in-progress jobs from the Jobs page.

### Querying

**Q: How accurate are the answers?**
A: Answers are generated from your documents with citations. Always verify important facts.

**Q: Can I ask questions about multiple documents?**
A: Yes, select multiple documents or query all documents at once.

**Q: What if the answer is wrong?**
A: Check the source citations. Rephrase your question or consult the original document.

**Q: Are queries logged?**
A: Yes, for analytics purposes. You can view your query history in the Analytics dashboard.

### Analytics

**Q: What data is collected?**
A: Query questions, response times, success rates, and document usage. No query answers are stored.

**Q: Can I delete my analytics data?**
A: Yes, through Profile → Data Export & Delete.

**Q: How often does the dashboard update?**
A: You can enable auto-refresh for 30-second updates or refresh manually.

### Billing & Plans

**Q: Is there a free tier?**
A: Yes, with limits on storage and queries. See Plans & Pricing for details.

**Q: How do I upgrade my plan?**
A: Go to Profile → Subscription and select your desired plan.

**Q: Can I downgrade?**
A: Yes, downgrades take effect at the end of your billing cycle.

---

## Appendix

### Keyboard Shortcuts

- `Ctrl/Cmd + K` - Focus search
- `Ctrl/Cmd + U` - Quick upload
- `Ctrl/Cmd + /` - Show shortcuts
- `Esc` - Close modal

### Document Processing Limits

| Metric | Free | Pro |
|--------|------|-----|
| Max file size | 50 MB | 100 MB |
| Total storage | 100 MB | 10 GB |
| Concurrent jobs | 3 | 100 |
| Processing priority | Normal | High |

### Query Limits

| Metric | Free | Pro |
|--------|------|-----|
| Queries per month | 500 | Unlimited |
| Max documents per query | 10 | 100 |
| Response timeout | 30s | 60s |
| API access | No | Yes |

---

**Need more help?** Contact support or check the [developer documentation](CLAUDE.md).
