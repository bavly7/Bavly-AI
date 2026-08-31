# Agentic RAG Retail Analytics — Challenges

## Challenge 1: Bridging disparate data sources

Because Bavly didn't have access to a real, unified supermarket dataset,
the sales tabular data and the CV video feeds came from different,
disconnected contexts. To make cross-domain queries logically consistent
— e.g. "if I discount the products in the aisle shown in camera 2, what's
the expected sales impact?" — he had to creatively map specific product
categories from the tabular sales data to physical aisles visible in the
video feed, so the system could reason across both sources coherently
rather than treating them as unrelated.

## Challenge 2: Integrating a classical ML model as an agent tool

The second, more technical challenge was integrating the LightGBM
forecasting model with the LLM agent — Bavly's first time orchestrating
an agent to actively use an ML model as a callable tool rather than just
retrieving text.

The agent had to accurately extract all necessary features (discount
rate, date, product ID) from the user's natural-language prompt. The
hardest part specifically was the fallback logic: when the user's prompt
was missing a required feature, the agent needed to recognize that gap
and dynamically ask the user for the missing parameter — instead of
either failing outright or hallucinating a plausible-sounding value to
fill the gap. Getting an agent to reliably notice "I don't have enough
information to call this tool correctly" and ask a clarifying question,
rather than guessing, took deliberate design work rather than being an
out-of-the-box LangChain behavior.
