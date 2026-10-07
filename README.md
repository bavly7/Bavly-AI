# Bavly AI Portfolio

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://github.com/langchain-ai/langgraph)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue.svg)](https://github.com/pgvector/pgvector)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**An intelligent AI-powered portfolio chatbot that answers questions about experience, projects, and skills using RAG (Retrieval-Augmented Generation)**

[Demo](https://bavly7.github.io/bavlywaleed.github.io/) • [Documentation](#documentation) • [Installation](#installation)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Improvements & Next Updates](#improvements--next-updates)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🌟 Overview

**Bavly AI Portfolio** is an interactive, intelligent chatbot that represents a personal portfolio. It leverages advanced RAG (Retrieval-Augmented Generation) technology with LangGraph orchestration to provide accurate, context-aware responses about professional background, certifications, skills, and projects.

### Key Highlights

- 🤖 **Intelligent Conversational AI** - Natural language understanding with context-aware responses
- 🔍 **RAG-Powered Knowledge Base** - Grounded answers with source traceability
- 🌐 **Multilingual Support** - Egyptian Arabic and English with automatic language detection
- 🎙️ **Voice Integration** - Speech-to-text and text-to-speech capabilities
- 🔄 **Auto-Sync with GitHub** - Webhook-based knowledge base updates
- 🚀 **High Performance** - Optimized retrieval with semantic caching
- 🎯 **Zero Hallucination** - Strict confidence thresholds and fallback mechanisms

---

## ✨ Features

### Core Capabilities

#### 🧠 Advanced RAG System
- **Multi-Entity Query Support** - Handle complex queries across multiple projects and companies
- **Semantic Search** - Vector-based similarity search using pgvector
- **Confidence Scoring** - Fallback to "I don't know" when confidence is low
- **Source Attribution** - Every answer is traceable to its knowledge source

#### 🎯 LangGraph Orchestration
- **Intelligent Routing** - Dynamic query classification and routing
- **Semantic Caching** - Cache similar queries to reduce latency and costs
- **Security Filtering** - Block inappropriate or out-of-scope queries
- **Multi-Intent Detection** - Handle complex queries with multiple intentions

#### 🌍 Multilingual Intelligence
- **Auto Language Detection** - Automatically detects Arabic or English
- **Context-Aware Responses** - Maintains language consistency throughout conversation
- **Egyptian Arabic Support** - Native dialect understanding

#### 🎙️ Voice Capabilities (Phase 5)
- **Speech-to-Text** - Convert voice input to text queries
- **Text-to-Speech** - Natural voice responses using edge-TTS
- **Voice Mode Detection** - Optimized responses for voice interactions

#### 🔄 GitHub Integration (Phase 3)
- **Webhook Receiver** - Auto-update knowledge base on repository changes
- **Diff-Based Re-Embedding** - Only re-process changed content
- **Project Metadata Sync** - Keep tech stacks and project info current

#### 📊 Advanced Filtering (Phase 5.1)
- **Technology-Based Search** - Find projects by specific tech stack
- **Project-Specific Queries** - Deep-dive into individual projects
- **Experience-Based Filtering** - Query by company or role
- **Mixed-Entity Comparisons** - Compare multiple projects or experiences

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                          │
│  (React + TypeScript - Conversational UI + Voice Recording)      │
└───────────────────────┬─────────────────────────────────────────┘
                        │ REST API / WebSocket
┌───────────────────────▼─────────────────────────────────────────┐
│                       FastAPI Backend                            │
│  • /chat - Main conversation endpoint                            │
│  • /webhook - GitHub integration endpoint                        │
│  • /stt, /tts - Voice I/O endpoints                             │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                    LangGraph Orchestration                       │
│                                                                   │
│  START → Language Detection → Security Check → Cache Check       │
│     │                                                             │
│     ├─ Cache Hit? → Return Cached Answer                        │
│     │                                                             │
│     └─ Cache Miss → Router (Intent Classification)              │
│             │                                                     │
│             ├─ Personal Query → Personal Bio Retrieval          │
│             ├─ Certification → Structured Cert Lookup           │
│             ├─ Project Query → Project-Specific Retrieval       │
│             ├─ Tech Search → Technology-Based Search            │
│             └─ Mixed Query → Multi-Source Parallel Retrieval    │
│                      │                                            │
│                      ▼                                            │
│              Confidence Check (Threshold: 0.65)                  │
│                      │                                            │
│         ┌────────────┴────────────┐                             │
│         ▼                          ▼                              │
│   High Confidence           Low Confidence                       │
│         │                          │                              │
│         ▼                          ▼                              │
│   Generate Answer          Fallback Response                     │
│   (with sources)           ("I don't know")                      │
│                                                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│               PostgreSQL + pgvector Database                     │
│                                                                   │
│  • knowledge_chunks - Embedded text chunks (1024-dim vectors)    │
│  • certifications - Structured certification data                │
│  • projects - Project metadata and tech stacks                   │
│  • sessions / messages - Conversation history                    │
│  • answer_cache - Semantic query cache                          │
└─────────────────────────────────────────────────────────────────┘
```

### LangGraph State Machine

The system uses a sophisticated state machine to handle queries:

1. **Language Detection** - Identifies Arabic or English
2. **Security Check** - Filters inappropriate queries
3. **Cache Lookup** - Checks for semantically similar cached queries
4. **Router** - Classifies intent and extracts entities
5. **Retrieval Nodes** - Parallel/sequential data fetching based on query type
6. **Confidence Check** - Validates retrieval quality
7. **Generation** - Produces grounded, source-attributed answers
8. **Response** - Saves to cache and returns to user

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - High-performance async web framework
- **LangGraph** - Orchestration and state management
- **SQLAlchemy** - ORM and database interactions
- **Alembic** - Database migrations

### AI & ML
- **Groq** - LLM inference (llama-3.3-70b-versatile)
- **Cohere** - Multilingual embeddings (embed-multilingual-v3.0)
- **pgvector** - Vector similarity search in PostgreSQL

### Database
- **PostgreSQL 15+** - Primary database
- **pgvector Extension** - Vector operations and indexing

### Voice
- **edge-TTS** - Text-to-speech synthesis
- **Groq Whisper** - Speech-to-text transcription

### DevOps & Tools
- **Git** - Version control
- **GitHub Webhooks** - Auto-sync mechanism
- **python-dotenv** - Environment configuration
- **pandas** - Data processing

---

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ with pgvector extension
- Git
- Virtual environment tool (venv or virtualenv)

### Step 1: Clone the Repository

```bash
git clone https://github.com/bavly7/portfolio.git
cd portfolio
```

### Step 2: Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Database Setup

1. **Install PostgreSQL** (if not already installed)
2. **Enable pgvector extension**:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. **Run migrations**:

```bash
alembic upgrade head
```

### Step 5: Populate Knowledge Base

```bash
# Populate database with initial knowledge
python scripts/populate_db.py

# (Optional) Backfill metadata if migrating from older schema
python backend/backfill_metadata.py
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/portfolio_db

# API Keys
GROQ_API_KEY=your_groq_api_key_here
COHERE_API_KEY=your_cohere_api_key_here

# Model Configuration
ROUTER_MODEL=openai/gpt-oss-120b
GROQ_MODEL=openai/gpt-oss-120b
SECURITY_MODEL=openai/gpt-oss-120b

# CORS (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-domain.com

# GitHub Webhook (optional)
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Cache Configuration (optional)
CACHE_SIMILARITY_THRESHOLD=0.92
CACHE_TTL_HOURS=168

# Retrieval Configuration (optional)
CONFIDENCE_THRESHOLD=0.65
MAX_CHUNKS_PER_ENTITY=3
```

### Getting API Keys

1. **Groq API Key**: Sign up at [console.groq.com](https://console.groq.com/)
2. **Cohere API Key**: Sign up at [cohere.com](https://cohere.com/)
3. **Database**: Use [Supabase](https://supabase.com/) (free tier) or local PostgreSQL

---

## 🚀 Usage

### Starting the Backend Server

```bash
# Development mode with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Chat Endpoint

```bash
POST /chat
Content-Type: application/json

{
  "session_id": "optional-session-id",
  "query": "What projects have you worked on with Python?",
  "history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

**Response:**
```json
{
  "answer": "I've worked on several Python projects...",
  "sources": ["project_narrative", "personal_bio"],
  "certificate_links": [],
  "profile_links": [...],
  "language": "en"
}
```

#### 2. Voice Input (Speech-to-Text)

```bash
POST /stt
Content-Type: multipart/form-data

audio: <audio file (wav/mp3/webm)>
```

#### 3. Voice Output (Text-to-Speech)

```bash
POST /tts
Content-Type: application/json

{
  "text": "Hello, I'm Bavly",
  "language": "en"
}
```

#### 4. GitHub Webhook

```bash
POST /webhook/github
Content-Type: application/json
X-Hub-Signature-256: <signature>

{
  "repository": {...},
  "commits": [...]
}
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

---

## 📁 Project Structure

```
portfolio/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration scripts
│   └── env.py                  # Alembic configuration
├── backend/                    # Backend application
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── graph.py                # LangGraph orchestration logic
│   ├── retrieval.py            # RAG retrieval functions
│   ├── generation.py           # Answer generation logic
│   ├── ingestion.py            # Knowledge base ingestion
│   ├── webhook.py              # GitHub webhook handler
│   ├── voice.py                # STT/TTS functions
│   ├── models.py               # Database models
│   └── backfill_metadata.py    # Migration helper scripts
├── content/                    # Static content (if any)
├── docs/                       # Documentation
│   ├── SPECS.md                # Architecture specifications
│   ├── RULES.md                # Development rules
│   ├── TASKS.md                # Project tasks and phases
│   ├── PHASE3_WEBHOOK_SETUP.md # Webhook setup guide
│   ├── PHASE5_VOICE_SETUP.md   # Voice feature guide
│   └── TOKEN_OPTIMIZATION.md   # Performance optimization
├── frontend/                   # Frontend application
│   ├── index.html              # Main HTML file
│   └── character/              # Character assets
├── knowledge/                  # Knowledge base source files
│   └── personal/               # Personal information
│       ├── bio.md
│       ├── education.md
│       ├── goals.md
│       └── skills.md
├── scripts/                    # Utility scripts
│   ├── populate_db.py          # Initialize database with knowledge
│   ├── backfill_file_paths.py  # Migration helper
│   ├── fix_project_metadata.py # Maintenance script
│   └── clear_cache.py          # Cache management
├── tests/                      # Test suite
│   ├── test_retrieval.py       # Retrieval tests
│   ├── test_queries.py         # Query tests
│   ├── test_voice.py           # Voice feature tests
│   ├── test_webhook.py         # Webhook tests
│   └── stress_test_rag.py      # Performance tests
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 📚 API Documentation

### Request/Response Models

#### ChatRequest
```python
{
  "session_id": str (optional),
  "query": str (required),
  "history": list[dict] (optional)
}
```

#### ChatResponse
```python
{
  "answer": str,
  "sources": list[str],
  "certificate_links": list[dict],
  "profile_links": list[dict],
  "language": str
}
```

### Query Types Supported

1. **Personal Queries** - About background, bio, goals
2. **Certification Queries** - Specific certifications and credentials
3. **Project Queries** - Project-specific deep dives
4. **Technology Search** - Find projects by tech stack
5. **Experience Queries** - Company and role-specific questions
6. **Mixed Queries** - Complex multi-entity comparisons

---

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_retrieval.py

# Run with verbose output
pytest -v tests/

# Run stress tests
python tests/stress_test_rag.py
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Adding New Knowledge

1. **Add structured data** to `scripts/populate_db.py`
2. **Add narrative content** to `knowledge/` directory
3. **Run ingestion**: `python scripts/populate_db.py`

### Code Style

The project follows Python best practices:
- Type hints for function signatures
- Docstrings for modules and complex functions
- Clear separation of concerns
- Comprehensive error handling

---

## 🧪 Testing

### Test Coverage

- **Unit Tests** - Individual function testing
- **Integration Tests** - End-to-end query flow
- **Stress Tests** - Performance and load testing
- **Voice Tests** - STT/TTS validation
- **Webhook Tests** - GitHub integration testing

### Running Specific Test Suites

```bash
# Test retrieval system
pytest tests/test_retrieval.py -v

# Test voice features
pytest tests/test_voice.py -v

# Test webhook integration
pytest tests/test_webhook.py -v

# Run stress test and generate report
python tests/stress_test_rag.py
```

### Test Results

Test results and performance metrics are saved in `tests/` directory with timestamps.

---

## 🚢 Deployment

### Backend Deployment Options

1. **Railway** (Recommended for free tier)
   - Connect GitHub repository
   - Add environment variables
   - Deploy automatically on push

2. **Render**
   - Free tier available
   - PostgreSQL included
   - Auto-deploy from GitHub

3. **Fly.io**
   - Good free tier
   - Edge deployment
   - Simple CLI deployment

### Frontend Deployment

1. **Vercel** (Recommended)
   - Zero configuration
   - Global CDN
   - Automatic HTTPS

2. **Netlify**
   - Drag-and-drop deployment
   - Continuous deployment
   - Free SSL

3. **GitHub Pages**
   - Free hosting
   - Custom domain support
   - Direct from repository

### Environment Setup for Production

```bash
# Set production environment variables
DATABASE_URL=<production_database_url>
GROQ_API_KEY=<your_key>
COHERE_API_KEY=<your_key>
ALLOWED_ORIGINS=https://your-domain.com
```

### GitHub Webhook Setup

1. Go to repository Settings → Webhooks
2. Add webhook URL: `https://your-backend.com/webhook/github`
3. Set content type: `application/json`
4. Select events: `push` and `pull_request`
5. Add secret token to `.env` as `GITHUB_WEBHOOK_SECRET`

---

## 🔮 Improvements & Next Updates

The following enhancements are planned or in progress to further improve the system:

### 1. 🎯 Add `source_types` to GraphState and Router Output

**Status:** Planned  
**Priority:** High  
**Description:**

Currently, the router classifies queries and determines what to retrieve, but doesn't explicitly pass `source_types` through the state. This enhancement will:

- Add `source_types: list[str]` field to `GraphState`
- Have the router explicitly output which source types to query (`personal_bio`, `project_narrative`, `experience`, `certification`, etc.)
- Enable better tracking of retrieval sources throughout the graph
- Improve debugging and logging of retrieval decisions
- Support more granular retrieval strategies

**Benefits:**
- Clearer data flow through the graph
- Better source attribution in responses
- Easier to add new source types in the future
- Improved observability of retrieval process

---

### 2. 🔧 Extend Technology Retrieval to Support Experiences

**Status:** In Progress  
**Priority:** High  
**Description:**

The current `find_projects_by_tech()` function only searches the `projects` table. This enhancement will:

- Create a new `find_experiences_by_tech()` function to search experience entries
- Support queries like "What experience do you have with React?" or "Which companies did you use Python at?"
- Add experience-based technology filtering to the router logic
- Enable cross-entity tech queries (both projects AND experiences)
- Update the retrieval node to handle experience-based tech searches

**Implementation:**
```python
# New function in retrieval.py
def find_experiences_by_tech(tech_terms: list[str], limit: int = 5) -> list[dict]:
    """
    Find work experiences that used specific technologies.
    Searches experience chunks for tech stack mentions.
    """
    # Implementation details...
```

**Benefits:**
- More comprehensive technology-based search
- Better answers to "Where have you used X?" questions
- Fuller picture of technology experience across career
- Supports comparison queries across projects and jobs

---

### 3. ✅ Add an Answer Validation Node

**Status:** Planned  
**Priority:** Medium  
**Description:**

Add a post-generation validation step to ensure answer quality and grounding. This node will:

- Verify that generated answers are grounded in retrieved context
- Check for potential hallucinations or unsupported claims
- Validate that sources cited actually support the claims made
- Flag low-confidence answers for fallback response
- Ensure language consistency (answer matches query language)

**Graph Position:**
```
generate_answer → validate_answer → respond
                       ↓ (validation fails)
                  fallback_response
```

**Validation Checks:**
- ✓ Answer contains only information from retrieved chunks
- ✓ Citations match actual chunk content
- ✓ No general knowledge mixed with personal claims
- ✓ Answer is in correct language
- ✓ Tone is appropriate for query type

**Benefits:**
- Dramatically reduces hallucination risk
- Ensures higher quality responses
- Better user trust and confidence
- Clearer separation between grounded and uncertain answers

---

### 4. 🎙️ Update Voice Integration

**Status:** Planned  
**Priority:** Medium  
**Description:**

Enhance the existing voice capabilities with several improvements:

#### 4.1 Voice Mode Optimization
- Optimize prompts specifically for voice interactions (shorter, more natural responses)
- Add voice-specific response templates
- Improve handling of voice ambiguities

#### 4.2 Multi-Language Voice Support
- Expand edge-TTS voice options for Arabic (male/female voices)
- Add voice selection API endpoint
- Support voice customization per user preference

#### 4.3 Real-Time Streaming
- Implement streaming TTS for faster response time
- Add WebSocket endpoint for real-time voice chat
- Support partial audio playback while generating

#### 4.4 Voice Activity Detection
- Add silence detection to auto-stop recording
- Implement noise cancellation preprocessing
- Better handling of background noise

#### 4.5 Voice Analytics
- Track voice usage metrics
- Measure voice query accuracy vs. text queries
- A/B test voice response formats

**Technical Changes:**
```python
# Enhanced voice.py
async def text_to_speech_streaming(text: str, language: str, voice: str):
    """Stream TTS audio in chunks for faster playback"""
    
async def speech_to_text_with_vad(audio: bytes):
    """STT with voice activity detection"""
```

**Benefits:**
- Better user experience for voice interactions
- Lower latency for voice responses
- More natural voice conversations
- Improved accessibility

---

### Additional Planned Features

#### 🔍 Advanced Analytics Dashboard
- Track popular questions and topics
- Monitor retrieval performance metrics
- Visualize conversation patterns
- A/B test different prompt templates

#### 🌐 Multi-Modal Support
- Support image uploads (CV, certificates, diagrams)
- OCR integration for document parsing
- Visual project showcase integration

#### 🤝 Conversation Memory Enhancement
- Long-term user preference storage
- Context-aware follow-up questions
- Personalized response styles per user

#### 🔐 Enhanced Security
- Rate limiting per IP/session
- Advanced prompt injection detection
- Content filtering for sensitive topics
- Audit logging for compliance

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Provide detailed reproduction steps
3. Include error messages and logs
4. Specify your environment (Python version, OS, etc.)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain why it would be valuable
4. Consider implementation complexity

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit with clear messages (`git commit -m 'Add AmazingFeature'`)
7. Push to your fork (`git push origin feature/AmazingFeature`)
8. Open a Pull Request

### Development Guidelines

- Follow existing code style and patterns
- Add type hints to function signatures
- Write docstrings for new functions
- Update tests and documentation
- Respect the rules in `docs/RULES.md`
- Follow the architecture in `docs/SPECS.md`

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Contact

**Bavly Waleed**

- 🌐 Portfolio: [bavly7.github.io](https://bavly7.github.io/bavlywaleed.github.io/)
- 💼 LinkedIn: [linkedin.com/in/bavly-waleed](https://www.linkedin.com/in/bavly-waleed)
- 🐙 GitHub: [github.com/bavly7](https://github.com/bavly7)
- 📊 Kaggle: [kaggle.com/bavlywaleed](https://www.kaggle.com/bavlywaleed)
- 📧 Email: bavly.waleed777@gmail.com
- 📱 Phone: +20 120 002 0385

---

## 🙏 Acknowledgments

- **LangChain/LangGraph** - For the excellent orchestration framework
- **Groq** - For fast and free LLM inference
- **Cohere** - For multilingual embedding models
- **Supabase** - For PostgreSQL hosting with pgvector
- **FastAPI** - For the high-performance web framework
- **Open Source Community** - For the amazing tools and libraries

---

## 📊 Project Stats

- **Total Lines of Code:** ~3,500+
- **Test Coverage:** Comprehensive test suite with unit, integration, and stress tests
- **API Response Time:** <500ms average (with caching)
- **Supported Languages:** 2 (Arabic, English)
- **Knowledge Sources:** 4+ types (bio, projects, certifications, experiences)
- **Deployment:** Zero-cost free-tier stack

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by [Bavly Waleed](https://github.com/bavly7)

</div>
