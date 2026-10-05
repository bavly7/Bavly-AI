# Movie Recommendation AI Assistant — Technical Decisions

## Embedding Model Selection
- Chose sentence-transformers/all-MiniLM-L6-v2 for balance between speed and accuracy
- 384-dimension embeddings suitable for semantic movie search
- Pre-trained model requiring no additional training

## Vector Store Choice
- Selected FAISS over alternatives (Pinecone, Qdrant) for local deployment
- Flat index for exact search without approximation
- Acceptable performance for 44K documents

## Agent Framework
- LangChain ReAct pattern for tool-using capabilities
- Iterative reasoning and action execution
- Built-in tool orchestration and state management

## Memory Strategy
- Rolling window (4 messages) to balance context and token efficiency
- JSON persistence for session recovery
- Full backup for conversation history analysis

## Watchlist Storage
- Excel format for easy user inspection and manual editing
- Simple read/write operations with pandas
- No database overhead for small personal datasets

## Fuzzy Matching
- Implemented for handling typos in movie titles
- Alternative suggestions when exact matches fail
- Improved user experience for ambiguous queries
