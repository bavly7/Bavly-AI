# LeadFlow AI — Architecture

## Three-Agent Pipeline

### Agent 1: Prospector
- **Role**: Lead Discovery
- **Input**: Search query (e.g., "restaurants in Cairo Egypt")
- **Process**: Web search for potential business leads
- **Output**: List of company names and URLs

### Agent 2: Scraper & Qualifier
- **Role**: Contact Extraction & Lead Qualification
- **Input**: Company URLs from Agent 1
- **Process**: 
  - Scrapes website content
  - Extracts contact email using LLM
  - Qualifies lead (checks if they lack AI chatbot)
- **Output**: Qualified leads with contact emails in SQLite database

### Agent 3: Closer
- **Role**: Email Generation & Delivery
- **Input**: Qualified leads from database
- **Process**:
  - Generates personalized cold email using Groq LLM
  - Sends via Gmail SMTP
  - Marks lead as emailed in database
- **Output**: Sent emails tracked in database

## LangGraph Workflow

```
START → Prospector → Scraper & Qualifier → Conditional Check
                                              ↓
                                    Any qualified leads?
                                         /        \
                                      Yes          No
                                       ↓            ↓
                                    Closer        END
                                       ↓
                                     END
```

## Data Flow

```
Search Query → Web Search → Lead URLs → Website Scraping → Content Analysis
    → LLM Qualification → SQLite Storage → Email Generation → SMTP Delivery
```

## Technology Integration

- **LangGraph**: Multi-agent orchestration with conditional routing
- **Groq**: LLM for qualification and email generation
- **Pydantic**: Structured output validation
- **SQLite**: Lead tracking and state management
- **SMTP**: Automated email delivery via Gmail
