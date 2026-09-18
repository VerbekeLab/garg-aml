# Quickstart

No data download: `smurfing_graph` builds a network with known patterns so you
can see the score work before pointing it at anything of your own.

## Score a synthetic network

```pycon
>>> import garg_aml as ga
>>> graph, labels = ga.smurfing_graph(n_nodes=100, n_patterns=2, seed=1)
>>> graph.number_of_nodes(), int(labels.sum())
(109, 13)

```

109 accounts, 13 of them part of an injected smurfing pattern. Score them all:

```pycon
>>> scores = ga.score(graph)["GARGAML"]
>>> top10 = scores.sort_values(ascending=False, kind="stable").head(10).index
>>> int(labels.reindex(top10).sum())
8

```

Eight of the ten highest-scoring accounts are in a pattern, out of 13 among 109.
No training, no labels, no tuning.

## Score your own data

Most people have a table, not a graph:

```pycon
>>> import pandas as pd
>>> transactions = pd.DataFrame(
...     {
...         "payer": ["alice", "alice", "mule_a", "mule_b"],
...         "payee": ["mule_a", "mule_b", "bob", "bob"],
...         "amount": [900, 950, 890, 940],
...     }
... )
>>> scores = ga.score_edges(transactions, "payer", "payee")
>>> float(scores.loc["alice", "GARGAML"])
1.0

```

Only the two account columns are read. Amounts, timestamps and counts are
ignored — GARG-AML reads structure, and repeated transactions between the same
pair collapse to one edge.

## What the score means

Between -1 and 1, higher being more smurfing-like. A score of 1 is a textbook
pattern; a tightly-knit group whose members all trade with each other scores
around 0; an account with no neighbours left scores -1.

**Every account in a pattern scores high, not just the one sending the money.**
A mule's own neighbourhood has the same shape as the source's. Read a high
score as "this account sits in a smurfing-shaped subgraph".

See [Interpreting a score](guide/interpreting.md) before acting on any of this,
and [Limitations](limitations.md) before relying on it.

## Where next

- Large graph? [Preprocessing](guide/preprocessing.md) and [Scaling](scaling.md).
- Feeding a model? [Using scores as features](guide/features.md).
- Want alerts, not scores? [Turning scores into alerts](guide/alerts.md).
