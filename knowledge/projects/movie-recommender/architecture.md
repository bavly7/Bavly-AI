# Movie Recommendation AI Assistant — Architecture

The system uses a multi-layered architecture combining RAG, agentic workflows, and persistent state management.

## Core Components

### RAG Core
- **Dataset**: 44,503 movies from TMDB vectorized using sentence-transformers/all-MiniLM-L6-v2
- **Vector Store**: FAISS with flat index
- **Search**: Semantic similarity search with cosine distance

### Agent System
- **Framework**: LangChain ReAct pattern
- **Tools**: 6 specialized tools for movie operations
  - search_movies: Semantic search across movie database
  - add_to_watchlist: Add movies to personal watchlist
  - mark_watched: Mark movies as watched with ratings
  - cancel_movie: Remove movies from watchlist
  - view_watchlist: Display filtered watchlist
  - get_recommendations: Personalized recommendations based on viewing history

### Memory Management
- **Window**: Rolling 4-message memory
- **Persistence**: JSON file storage
- **Backup**: Full conversation history maintained

### Data Persistence
- **Watchlist**: Excel (.xlsx) file storage
- **Memory**: JSON file with conversation state
- **Logs**: Performance monitoring and error logging

## Data Flow

```
User Query → Memory Manager → ReAct Agent → Tool Selection → Tool Execution
    → (FAISS Search | Watchlist Operations | Recommendation Engine)
    → Response Generation → Memory Update → User Response
```
