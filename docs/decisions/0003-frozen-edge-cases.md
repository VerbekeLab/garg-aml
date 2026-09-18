# 0003 — Three degenerate cases return fixed values

**Decision.** These are preserved exactly as the pre-extraction code computed
them:

| Case | Value |
|---|---|
| Off-diagonal block with no free entries | density **1** |
| All block sizes zero (undirected) | score **-1** |
| Node with no neighbours | **0** for all four neighbour statistics |

**Context.** All three arise on tiny or isolated neighbourhoods. The third was
implemented as a bare `except:` around a numpy reduction over an empty list; it
is now an explicit branch with the same result.

**Why.** They produced the published numbers. Each is also defensible on its own
terms: an empty penalty block should not penalise, a node with no structure is
maximally far from smurfing, and a node with no neighbours has no neighbourhood
statistics to report. But the reason they are *frozen* is reproducibility, not
elegance.

**Consequence.** Changing any of them changes every published result. They look
like bugs and will attract cleanup; the golden fixtures under `tests/golden/`
fail loudly if one is touched. Louvain reduction leaves many isolated nodes
behind — 18 of the 24 in the toy fixture — so these paths are exercised far more
often than their obscurity suggests.
