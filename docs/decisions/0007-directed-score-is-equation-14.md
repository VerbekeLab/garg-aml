# 0007 — The directed score is Eq. 14, without the transpose-max

**Decision.** For a directed graph, `score()` returns Equation (14):

```
mean(score01, score12)
  - mean(score00, score02, score10, score11, score20, score21, score22)
```

The `max(score, score_transposed)` step found in the old
`GARG_AML_node_directed` is **not** ported.

**Context.** The pre-extraction code computed three directed quantities:
`GARGAML` (Eq. 14 as given), `GARGAML_transposed`, and `GARGAML_max`. The
experiments used the first; the serial convenience function returned the third.
On a 245-node synthetic graph the two differ for 205 nodes, so the choice is
material rather than cosmetic.

**Why.** Section 3.3 of the paper defines the score as Eq. 14 and contains no
max-with-transpose step. Reverse flow is handled one level up, in the **level
assignment**: Eq. (11) plus "we repeat this selection on the reversed network",
so a node at distance two sits at level 0 when no directed path of length two
reaches it in either direction. That rule is implemented, and is retained. The
transpose-max was an undocumented extra reachable only through a code path no
experiment called.

**Consequence.** Do not "restore" the max. It is not the paper's reverse-flow
handling, and it was never in the published pipeline.

**Related.** `GARGAML_max` named two different quantities in the old code — this
transpose-max, and the maximum score among a node's neighbours. In the directed
feature pipeline the second silently overwrote the first, which was harmless
because only the neighbour statistic was ever used as a feature. Here only the
neighbour statistic carries the name.
