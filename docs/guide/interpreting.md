# Interpreting a score

## The range

| Score | Structure |
|---|---|
| **1** | a textbook pattern: on-diagonal blocks empty, off-diagonal full |
| **~0.5** | clearly smurfing-shaped, with some background activity mixed in |
| **~0** | ordinary: a group that trades among itself scores here |
| **-1** | no neighbourhood at all — nothing to measure |

The score is a **structural resemblance, not a probability**. 0.8 does not mean
80% likely to be laundering. It means this account's neighbourhood looks 80% of
the way towards the idealised pattern, on a scale where a clique sits near 0.

## Scores are comparable within a run, not across runs

Two things change the scale underneath you: the preprocessing
([`reduce_graph`](preprocessing.md) changes which neighbourhoods exist) and the
`score_type`. Comparing a score computed on a reduced graph against one computed
on the full graph is meaningless. Fix both before comparing anything.

## Everyone in the pattern scores high

A mule's neighbourhood has the same block structure as the source's: its
counterparties (source and target) do not deal with each other. So the mules
score as high as the account that organised the scheme, sometimes higher.

Read a high score as **"this account sits in a smurfing-shaped subgraph"**, and
expect to investigate the subgraph rather than the single account. Pull the
account's second-order neighbourhood and look at it.

## Ties

**The score ties heavily**, especially at the top. Many accounts land on exactly
1.0 — in the paper's bank-level analysis, 522 of one institution's 2,639
customers shared exactly 1.0.

This matters the moment you rank. `sort_values().head(50)` will silently break
those ties by whatever order the frame happens to be in, which is an artefact of
your data loading, not a signal. If you take a top-K, check how many accounts
sit at the boundary score first:

```python
scores = ga.score(graph)["GARGAML"]
cutoff = scores.nlargest(50).min()
print((scores == cutoff).sum(), "accounts tied at the cut-off")
```

If that number is large, the top-50 is not 50 accounts — it is an arbitrary
50 drawn from a bigger tied set. Break the tie on something you trust
(transaction volume, exposure, customer risk rating) rather than on sort order.

## Why did this account score high?

Ask for the block measures:

```python
detailed = ga.score(graph, return_measures=True)
detailed.loc["account_of_interest"]
```

`measure_2` is the density of the off-diagonal block — how completely the
counterparties connect through. `measure_1` and `measure_3` are the on-diagonal
blocks that should be empty. A high score with a tiny `size_2` means the
pattern is real but tiny, and probably not interesting.

That decomposition is the point of the method: the score is always reducible to
a handful of interpretable densities.

## What a low score does not mean

A low score is not evidence of legitimacy. It means *this particular structure*
is absent. Laundering that does not route through mules — cash, trade
mis-invoicing, a single large transfer — has no reason to score high.
