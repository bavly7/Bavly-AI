# Movie Recommendation AI Assistant — Overview

An intelligent movie recommendation assistant that combines RAG architecture, LangChain agents, FAISS vector search, and conversational memory into a production-oriented conversational agent.

The system manages a personal watchlist, tracks viewing history, provides personalized recommendations, and executes multi-step tasks using ReAct agents across a dataset of 44,503 movies from TMDB.

**Dataset:** 44,503 movies from The Movie Database (TMDB)
**Embedding Model:** sentence-transformers/all-MiniLM-L6-v2
**Vector Store:** FAISS with 44,503 indexed documents
**Search Capability:** Natural-language semantic search (e.g., "mind-bending sci-fi movies")
**Tools:** 6 specialized tools (search, watchlist management, recommendations)
**Memory:** Rolling 4-message window with JSON persistence
