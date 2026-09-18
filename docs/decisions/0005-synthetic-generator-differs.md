# 0005 — The synthetic generator does not reproduce the paper's datasets

**Decision.** `garg_aml.synthetic` is a fresh networkx implementation. The
igraph-based generator that produced the paper's 66 synthetic datasets stays in
the research repository.

**Context.** The original generator depends on igraph, and its graphs are
reproducible only under specific igraph versions and RNG seeds.

**Why.** Requiring igraph for a tutorial is a poor trade, and the package's
generator exists to serve documentation examples and tests — it needs to be
*reproducible*, not *identical to the paper's*. Chasing bit-for-bit parity would
have pinned an extra core dependency for no user-facing benefit.

**Consequence.** This is the one deliberate non-equivalence in the extraction.
Anything reproducing the paper's synthetic results must use the research
repository's generator. Do not "unify" the two.
