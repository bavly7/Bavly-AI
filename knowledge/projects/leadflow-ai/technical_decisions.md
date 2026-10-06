# LeadFlow AI — Technical Decisions

## Multi-Agent Architecture
- Chose LangGraph for explicit agent orchestration over implicit chaining
- Separated concerns: discovery, qualification, outreach
- Enabled conditional routing based on qualification results

## LLM Selection
- Selected Groq for fast inference and cost efficiency
- Used structured outputs with Pydantic for reliability
- Implemented retry logic for API stability

## Data Persistence
- Chose SQLite for simplicity and portability
- Avoided external database dependencies
- Sufficient for prototype and small-scale deployment

## Web Scraping Strategy
- Used requests + BeautifulSoup for simplicity
- Implemented error handling for diverse website structures
- Added rate limiting to avoid blocking

## Email Delivery
- Used Gmail SMTP with app passwords
- Implemented email state tracking to prevent duplicates
- Added error handling for delivery failures

## Structured Outputs
- Pydantic schemas for qualification and email generation
- Ensured type safety and validation
- Prevented malformed LLM outputs
