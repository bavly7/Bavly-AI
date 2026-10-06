# Agentic RAG Retail Analytics — Trade-offs

- **Pre-trained YOLO instead of a fine-tuned detector.** Traded
  potential accuracy gains from a custom-trained model for development
  speed — annotating a large dataset from this project's specific camera
  angles would have consumed time better spent on the tracking/zone-
  analysis logic and the agent orchestration layer, given the project
  timeline.
- **Simulated data instead of a real supermarket backend.** Without
  access to live retail data, sales and CV data had to be manually
  mapped together (aisle-to-category) to make cross-domain reasoning
  possible — a reasonable simulation for demonstrating the system's
  capability, but not validated against real, naturally-unified retail
  data.
- **LightGBM over a deep learning forecasting approach.** Prioritized
  speed and simplicity for tabular sales data over the potentially higher
  ceiling (but higher cost and complexity) of a deep learning forecasting
  model, given the CV pipeline and LLM agent were already resource-heavy
  parts of the same system.
