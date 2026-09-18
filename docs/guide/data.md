# Preparing your data

## What GARG-AML reads

Two columns: who paid, and who was paid. That is all.

Amounts, timestamps, currencies and transaction counts are **not** used. The
method reads the shape of the network. Repeated transactions between the same
pair of accounts collapse to a single edge, and self-transfers are dropped.

This is a real limitation as well as a strength — see
[Limitations](../limitations.md).

## From a table

```python
scores = ga.score_edges(transactions, "payer_account", "payee_account")
```

## From a graph

If you already build a networkx graph, pass it directly:

```python
scores = ga.score(graph)
```

Node ids come back exactly as you supplied them — strings, integers, tuples —
as the index of the returned frame, so you can join the scores straight back
onto your own tables.

## What counts as an account

Whatever you make a node. That choice matters more than any parameter in this
package:

- **One node per account** is the usual choice and what the paper evaluates.
- **One node per customer**, merging their accounts, will find schemes that
  spread across accounts of the same person — and will hide schemes that use
  several accounts of one customer as the mules.
- **One node per bank** is too coarse; the pattern disappears into aggregate.

## Directed or undirected?

Both are supported. `score()` follows the graph you give it: a `DiGraph` gets
the directed analysis, a `Graph` the undirected one.

Start with **undirected**. In the paper's experiments the undirected score
outperforms the directed one, which is counter-intuitive given that
one-directional flow is definitional for smurfing. The directed variant is
stricter about which accounts count as senders and receivers, and that
strictness appears to cost more than the extra information gains.

If you have direction, it is still worth trying both on your own data.

## Scale

Nothing here needs the whole graph in one piece conceptually, but networkx does
hold it in memory. For rough numbers and what to do about a graph that does not
fit, see [Scaling](../scaling.md).
