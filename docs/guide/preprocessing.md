# Preprocessing

Two optional steps. Neither is applied unless you ask.

## Community reduction

```python
reduced = ga.reduce_graph(graph, resolution=10)
scores = ga.score(reduced)

# or, equivalently
scores = ga.score(graph, reduce=True, resolution=10)
```

`reduce_graph` partitions the graph with Louvain and **keeps only the edges
whose endpoints are in the same community**. This is Algorithm 1 of the paper,
and it is how the published results were produced.

!!! warning "This is lossy, and the loss is large"
    On the paper's IBM dataset this removes the large majority of edges. It does
    not merely thin the graph — it changes which second-order neighbourhoods
    exist at all, and therefore which patterns *can* be found.

Why do it anyway? Cost. Scoring is driven by neighbourhood size, and in a dense
transaction network a handful of hub-adjacent accounts have enormous
neighbourhoods. Cutting between-community edges makes those tractable.

### Choosing a resolution

Higher resolution means smaller communities and so more edges cut.

```pycon
>>> import networkx as nx
>>> import garg_aml as ga
>>> graph = nx.disjoint_union(nx.complete_graph(4), nx.complete_graph(4))
>>> graph.add_edge(0, 4)
>>> ga.reduce_graph(graph, resolution=1).number_of_edges()
12
>>> ga.reduce_graph(graph, resolution=10).number_of_edges()
0

```

Two cliques joined by one edge. At resolution 1 the bridge is cut and both
cliques survive. At the published resolution of 10 the communities are smaller
than a clique, so **every** edge goes and all eight accounts are left isolated.

Nothing is dropped — isolated accounts remain in the output and score -1 — but
they can no longer be scored meaningfully. If a large share of your accounts
come back at -1, the resolution is too high for your data.

The default is 10 because that is what the paper used. It is not a
recommendation for your network. Sweep it and look at how many accounts survive
with a neighbourhood.

## Hub removal

```python
pruned = ga.drop_hubs(graph, quantile=0.01)
```

Removes the highest-degree accounts — payment processors, exchanges, salary
accounts — which have huge neighbourhoods and are rarely what you are looking
for. Not part of the published pipeline, but useful when a few accounts
dominate the runtime.

Note that accounts at the threshold degree are all removed, so ties can push the
number removed above the nominal fraction.

## Reproducibility

Both steps are deterministic given a seed. `reduce_graph` takes `seed=1997` by
default — the value used throughout the paper — because Louvain is otherwise
not reproducible run to run. Keep it fixed when comparing runs.
