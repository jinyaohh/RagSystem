# Documentation Index

Welcome to the Financial RAG System documentation!

## 📚 Documentation Structure

### For Users

- **[Quick Start Guide](../QUICKSTART.md)** - Get up and running in 10 minutes
- **[User Manual](../USER_MANUAL.md)** - Comprehensive guide to all features
- **[README](../README.md)** - Project overview and features

### For Developers & Maintainers

- **[Developer Guide (CLAUDE.md)](../CLAUDE.md)** - Architecture, development setup, contributing
- **[Architecture](architecture/ARCHITECTURE.md)** - System design and technical details
- **[Quick Reference](guides/QUICK_REFERENCE.md)** - API examples and code snippets

### Setup Guides

#### Phase 1 - MVP (Quick Demo)
- Single-user system
- Synchronous processing
- No authentication required
- **Setup:** See [QUICKSTART.md](../QUICKSTART.md) Option 1

#### Phase 2 - Production
- Multi-user system with authentication
- Async background processing with Celery
- Job tracking and status monitoring
- **Setup:** [PHASE2_PRODUCTION.md](setup/PHASE2_PRODUCTION.md)

#### Phase 3 - Analytics Dashboard
- Comprehensive analytics and insights
- Query logging and performance monitoring
- Interactive charts and visualizations
- **Setup:** [PHASE3_ANALYTICS.md](setup/PHASE3_ANALYTICS.md)

### Additional Guides

- **[Roadmap](guides/ROADMAP.md)** - Future features and planned enhancements
- **[Deployment Guide](#)** - Production deployment strategies (coming soon)
- **[API Reference](#)** - Complete API documentation (see `/docs` endpoint)

### Archive

Historical planning documents and phase implementations:
- [docs/archive/](archive/) - Implementation plans, code reviews, technical comparisons

---

## Quick Navigation

### I want to...

**...get started quickly**
→ Read [QUICKSTART.md](../QUICKSTART.md)

**...understand how to use all features**
→ Read [USER_MANUAL.md](../USER_MANUAL.md)

**...set up a production multi-user system**
→ Read [setup/PHASE2_PRODUCTION.md](setup/PHASE2_PRODUCTION.md)

**...add analytics to my system**
→ Read [setup/PHASE3_ANALYTICS.md](setup/PHASE3_ANALYTICS.md)

**...contribute code or add features**
→ Read [CLAUDE.md](../CLAUDE.md)

**...understand the architecture**
→ Read [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)

**...see API examples**
→ Read [guides/QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md)

**...deploy to production**
→ Read [CLAUDE.md - Deployment section](../CLAUDE.md#deployment)

---

## Documentation by Role

### End Users
1. [QUICKSTART.md](../QUICKSTART.md) - Get started
2. [USER_MANUAL.md](../USER_MANUAL.md) - Learn all features
3. [setup/PHASE2_PRODUCTION.md](setup/PHASE2_PRODUCTION.md) - Multi-user setup
4. [setup/PHASE3_ANALYTICS.md](setup/PHASE3_ANALYTICS.md) - Analytics setup

### System Administrators
1. [setup/PHASE2_PRODUCTION.md](setup/PHASE2_PRODUCTION.md) - Production setup
2. [setup/PHASE3_ANALYTICS.md](setup/PHASE3_ANALYTICS.md) - Analytics configuration
3. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) - System design
4. [CLAUDE.md - Deployment](../CLAUDE.md#deployment) - Deployment guide

### Developers
1. [CLAUDE.md](../CLAUDE.md) - Development guide
2. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Architecture details
3. [guides/QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md) - Code examples
4. [CLAUDE.md - Contributing](../CLAUDE.md#contributing) - How to contribute

### Product Managers / Stakeholders
1. [README.md](../README.md) - Project overview
2. [guides/ROADMAP.md](guides/ROADMAP.md) - Future plans
3. [USER_MANUAL.md](../USER_MANUAL.md) - Feature capabilities
4. [setup/PHASE3_ANALYTICS.md](setup/PHASE3_ANALYTICS.md) - Analytics features

---

## Key Concepts

### Phases Explained

**Phase 1 (MVP):**
- Single-user demonstration
- Immediate document processing
- Local storage
- Perfect for testing and demos

**Phase 2 (Production):**
- Multi-user with authentication
- Background async processing
- Cloud storage (Supabase)
- Job tracking and monitoring
- Scalable architecture

**Phase 3 (Analytics):**
- Comprehensive usage analytics
- Query logging and insights
- Performance monitoring
- Interactive dashboards
- Activity tracking

### Tech Stack Overview

**Backend:**
- FastAPI (Python web framework)
- LangChain (RAG orchestration)
- Qdrant (Vector database)
- Supabase (PostgreSQL + Auth + Storage)
- Celery + Redis (Async task processing)
- OpenAI (GPT-4 + Embeddings)

**Frontend:**
- Next.js 14 (React framework)
- TypeScript (Type safety)
- Tailwind CSS (Styling)
- Recharts (Data visualization)
- shadcn/ui (UI components)

---

## Getting Help

**Documentation Issues:**
- Found an error? Open an issue on GitHub
- Missing information? Suggest improvements
- Want to contribute? See [CLAUDE.md - Contributing](../CLAUDE.md#contributing)

**Technical Support:**
- Check [USER_MANUAL.md - Troubleshooting](../USER_MANUAL.md#troubleshooting)
- Review [CLAUDE.md - Troubleshooting](../CLAUDE.md#troubleshooting)
- Open a GitHub issue for bugs
- Check existing issues for known problems

**Community:**
- GitHub Discussions for questions
- Contributing guidelines in CLAUDE.md
- Code examples in guides/

---

## Document Versioning

All documentation is version controlled with the code. Check git history for changes:

```bash
# See documentation changes
git log -- docs/

# View specific document history
git log -- docs/setup/PHASE2_PRODUCTION.md
```

---

**Last Updated:** November 2025
**Current Version:** 3.0 (Phase 3 - Analytics)
