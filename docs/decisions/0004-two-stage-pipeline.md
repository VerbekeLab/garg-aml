# 0004 — Scoring is two-stage, and there is only one implementation

**Decision.** The canonical path is `block_measures()` → `score_from_measures()`.
`score()` is a thin wrapper over both, never a parallel implementation.

**Context.** The pre-extraction code had two paths that computed the same thing:
a serial `GARG_AML(G)` convenience function, and the two-stage route that every
experiment actually used. They had drifted — see
[0007](0007-directed-score-is-equation-14.md).

**Why.** Two implementations of one formula is how the drift happened. The split
is also genuinely useful: block measures are the expensive part and are worth
persisting, and the cheap aggregation can then be re-run under a different
`score_type` without recomputing anything.

**Consequence.** A new aggregation or a new score variant extends stage two and
must never introduce a second stage one.
