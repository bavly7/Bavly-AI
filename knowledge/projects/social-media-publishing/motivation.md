# Social Campaign Publisher — Motivation

The original requirement during Bavly's FlyRank internship was fairly
basic: build a simple scheduled publisher in a sandbox environment that
takes a manually written caption and an image, and posts it based on a
timer.

He decided to take it much further. Instead of a basic scheduler, he
engineered a full "campaign-driven" system: support for different
campaign intents (promotional ads, educational content, opinion pieces),
each dynamically tailoring the generated content to fit the specific
characteristics and constraints of each platform. He also introduced a
human-in-the-loop feature — the system generates and schedules the
campaign, but the user reviews and can edit the content before it goes
live, giving absolute control and eliminating the risk of an LLM
hallucination reaching production unchecked.
