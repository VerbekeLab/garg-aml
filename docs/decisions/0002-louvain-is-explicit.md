# 0002 — Louvain reduction is a separate, opt-in step

**Decision.** `reduce_graph(graph, resolution=10, seed=1997)` is its own
function. `score()` does not reduce unless asked (`score(graph, reduce=True)`).

**Context.** The published pipeline partitions the graph with Louvain and keeps
only intra-community edges before scoring. On the IBM HI-Small data that removes
the large majority of edges.

**Why.** The step is **lossy** and it is a modelling choice, not an
implementation detail — it changes which neighbourhoods exist at all, and
reviewers of the paper questioned it directly. Burying it inside the scorer
would hide the single most consequential preprocessing decision from the person
interpreting a score, which is the opposite of what an interpretable method
should do.

**Consequence.** Users must decide. The documentation explains the trade-off
rather than choosing for them, and `resolution` has to be passed explicitly in
code that reproduces the paper, so a sweep over it is visible in the diff.
