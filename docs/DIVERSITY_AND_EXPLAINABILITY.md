# Diversity, Exploration & Explainability

This doc summarizes how the ranking pipeline balances engagement with diversity and how explainability supports auditability.

## Diversity & exploration

- **Author diversity** — The diversity scorer penalizes repeated authors in the candidate list so the feed does not collapse to a single voice even when one author has high engagement. Tunable via the *diversity strength* preference.
- **Exploration** — The out-of-network (Phoenix-style) source and the *friends vs global* slider inject content from accounts the user does not follow; increasing this parameter increases exploration and reduces in-group saturation.
- **Recency vs popularity** — Lower *recency vs popularity* favors newer posts over raw like/repost counts, so the feed stays fresh and is less dominated by a few viral items.
- **Topic weights** — Adjusting tech / politics / culture / memes / finance weights shifts which topics surface, so you can study how algorithmic emphasis shifts perceived discourse (e.g. more tech vs more politics).
- **Niche vs viral** — The *niche vs viral* control (with topic weights) lets you bias toward niche or viral-style content.

Together, these controls let you study how tuning the algorithm changes feed composition and emergent discourse patterns.

## Explainability

Every item in the ranked feed can be annotated with a **ranking explanation** (enable “Show why this post” in the UI):

| Field | Meaning |
|-------|--------|
| **Source** | Whether the post came from *Following* (in-network) or *For you* (out-of-network). |
| **Rank & score** | Position in the ranked list and the final score used for ordering. |
| **Diversity penalty** | How much the author-diversity term reduced the score when the same author appeared recently. |
| **Recency boost** | Contribution from post age. |
| **Topic boost** | Contribution from topic weights. |

The feed API returns these explanations when `include_explanations=true`. This supports reproducibility and research: you can record how a given set of preferences and engagement history produced a specific ordering, and reason about how changing weights would shift which posts appear and in what order.

## Auditability

- **Reproducibility** — Same user, preferences, and engagement state yield the same feed ordering (deterministic pipeline).
- **Inspectability** — Per-item explanations expose the scoring components (source, action scores, diversity, recency, topic) so you can audit why a post was ranked where it was.
- **Experimentation** — Sliders and topic weights let you run controlled experiments (e.g. more diversity vs more viral) and compare feed composition.

See also: README sections **Balancing engagement with diversity** and **Auditability & explainability**.
