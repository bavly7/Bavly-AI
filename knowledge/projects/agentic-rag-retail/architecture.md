# Agentic RAG Retail Analytics — Architecture

```
                   Cameras
                      │
                      ▼
             YOLO + Tracking
                      │
          Zone Analytics Engine
                      │
         Live Analytics (JSON API)
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
   Tool Calling              Vector Database
                                  │
                        Qdrant + Embeddings
                                  │
                     LangChain Agent (Llama-3)
                                  │
                ┌─────────────────┴────────────────┐
                ▼                                  ▼
         Live Retail QA                 Documentation QA
                                  │
                                  ▼
                      Sales Forecast Tool
                                  │
                                  ▼
                            Streamlit UI
```

## Components

- **Computer Vision Analytics Pipeline** — real-time customer tracking
  from live camera feeds using YOLO + multi-object tracking, generating
  zone occupancy, dwell-time, visitor counts, and heatmaps, exposed as a
  live analytics API.
- **Agentic RAG Assistant** — a LangChain tool-calling agent (Llama-3 via
  Groq) that routes manager questions to one of three tools: live CV
  analytics, a Qdrant vector store for documentation Q&A, or a LightGBM
  sales-forecasting tool — returning natural-language answers to
  scenario-style business questions.
- **Guardrails** — protection against prompt injection and off-topic
  queries (topical guard), keeping the assistant focused on retail
  analytics.
- **Observability** — LangSmith integrated for full tracing of agent tool
  calls and prompt execution, supporting debugging and prompt analysis.

## Tech Stack

| Category | Technologies |
|---|---|
| Computer Vision | YOLO, OpenCV |
| LLM | Llama-3 (Groq) |
| Framework | LangChain |
| Vector Database | Qdrant |
| Embeddings | HuggingFace |
| Forecasting | LightGBM |
| Backend | Python |
| Interface | Streamlit |
| Observability | LangSmith |
