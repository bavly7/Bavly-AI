# PulseFit — Challenges

## The hardest problem: bridging sports science with software engineering
at scale

The sheer scale of the domain logic was the hardest part — building
around 90 distinct exercise-tracking classes. The genuinely hard piece
wasn't the code volume itself, but taking complex fitness research
papers — specifically American College of Sports Medicine (ACSM)
guidelines — and translating those theoretical biomechanical rules into
deterministic baseline code that a program could actually execute
reliably per exercise.

Bavly designed the system so it relies on this strict scientific baseline
on day one, while continuously collecting performance data. Over time, it
was designed to learn from the individual user, transitioning from a
generic scientific baseline toward a more personalized system — because
every human body responds differently, and no static rule set can fully
capture that on its own.

## Other known rough edges (documented, not hidden)

- Team size vs. system scope: a 2-person team built computer vision pose
  detection, Franco-Arabic NLP, a recommendation engine, and full-stack
  development simultaneously — a genuinely large scope for the team size
  (see `learnings.md`).
- The ML-personalized version of the recommender (learning from actual
  user acceptance/progress data) is planned for V2, not yet built — V1
  remains fully rule-based.
