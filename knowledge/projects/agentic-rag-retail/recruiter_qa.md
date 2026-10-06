# Agentic RAG Retail Analytics — Recruiter Q&A

Q: Why LightGBM for forecasting instead of deep learning (like LSTM) or
Prophet?
A: Retail sales data is highly tabular and heavily dependent on
categorical features, lag features, and rolling statistics. LightGBM is
exceptionally fast, handles tabular data much better than deep learning
out-of-the-box, and is lightweight. Since the system was already running
a heavy CV pipeline and an LLM agent, the forecasting model needed to be
fast and efficient, not a heavy neural network.

Q: Why Qdrant for the vector database?
A: Qdrant is incredibly fast, written in Rust, and has excellent support
for payload (metadata) filtering. In a retail context, semantic search
isn't enough — you often need to filter by exact metadata (like
`category == 'beverages'` or `date > X`). Qdrant handles this hybrid
search seamlessly.

Q: Why didn't you fine-tune YOLO on your own supermarket footage?
A: Creating and annotating a large enough dataset from the project's
specific camera angles would have required significant effort for
uncertain accuracy gain. A strong pre-trained YOLO model combined with
custom tracking and zone-analysis logic achieved reliable performance
within the project's timeline — a deliberate scoping decision.

Q: How does the agent decide which tool to use for a given question?
A: The LangChain tool-calling agent routes based on the nature of the
question — live behavioral questions (traffic, dwell time) go to the CV
analytics tool, documentation-style questions go to the Qdrant vector
store, and hypothetical/scenario business questions go to the LightGBM
forecasting tool. The agent also has guardrails to refuse off-topic
questions and resist prompt injection attempts.
