# Agentic RAG Retail Analytics — Technical Decisions

## Why avoid full YOLO fine-tuning
Although a custom-trained detector could improve accuracy, creating and
annotating a large dataset from the project's specific supermarket camera
angles would require significant effort. Instead, Bavly leveraged a
strong pre-trained YOLO model and invested the time in developing custom
tracking and zone-analysis logic on top of it, achieving reliable
performance within the project's timeline — a deliberate effort trade-off,
not a limitation he was unaware of.

## Why LightGBM over deep learning (e.g. LSTM) or Prophet for forecasting
Retail sales data is highly tabular and heavily dependent on categorical
features, lag features, and rolling statistics — exactly what LightGBM
handles well out-of-the-box, while being exceptionally fast and
lightweight. Since the system was already running a heavy CV pipeline and
an LLM agent simultaneously, the forecasting component specifically
needed to be fast and efficient rather than adding another heavy neural
network into the stack.

## Why Qdrant for the vector database
Qdrant is fast, written in Rust, and has strong support for payload
(metadata) filtering. In a retail context, semantic search alone isn't
enough — queries often need to filter by exact metadata as well (e.g.
`category == 'beverages'` or `date > X`). Qdrant handles this hybrid
search (semantic + metadata filter) seamlessly, which a purely
similarity-based vector store would not.

## How the agent avoids hallucinating missing tool inputs
When a user's natural-language query is missing a parameter the
forecasting tool needs (e.g. discount rate, date, product ID), the agent
is designed to recognize the gap and dynamically ask the user for the
missing parameter, rather than failing silently or inventing a plausible-
looking value. This was a deliberate design goal, not an incidental
behavior — see `challenges.md` for how this was actually built.
