# Scaling

## What drives the cost

Each account is scored from its own second-order neighbourhood, independently of
every other account. So the cost is **not** a function of graph size directly —
it is the sum over accounts of the cost of their neighbourhood, and that is
dominated by the few accounts with very large ones.

For each account the work is: extract the second-order ego graph, build its
dense adjacency matrix, and sum over blocks. An account with *n* second-order
neighbours costs roughly *n²* to score. One account with 10,000 neighbours costs
as much as a million accounts with ten.

**This is why the tail matters more than the size.** A graph of ten million
ordinary retail accounts is easier than a graph of one million that includes a
payment processor.

## What to do about it

In order of how much they help:

1. **[Remove hubs](guide/preprocessing.md#hub-removal).** `drop_hubs` deletes
   the highest-degree accounts. A processor with a million counterparties is not
   the smurf you are looking for, and it single-handedly dominates the runtime.

2. **[Reduce the graph](guide/preprocessing.md#community-reduction).**
   `reduce_graph` cuts between-community edges, which shrinks the large
   neighbourhoods most. This is what makes the paper's larger dataset tractable.
   It is lossy — read that page before turning it on.

3. **Parallelise.** `n_jobs` spreads accounts across processes:

   ```python
   scores = ga.score(graph, n_jobs=-1)  # needs the `parallel` extra
   ```

   Because each account is independent this scales close to linearly in CPU. The
   catch is memory: every worker gets its own copy of the graph, so peak memory
   is roughly `n_jobs` times the graph. On a large graph that, not CPU, is the
   binding constraint — raise `n_jobs` until memory says stop, not until cores
   run out.

4. **Split the work.** The expensive stage is separable:

   ```python
   measures = ga.block_measures_frame(graph, n_jobs=-1)
   measures.to_parquet("measures.parquet")  # the expensive part, done once
   scores = ga.scores_from_measures(measures)  # seconds, any time after
   ```

   Worth doing on anything large: re-deriving scores under a different
   `score_type`, or rebuilding features, then costs nothing.

## Memory

networkx holds the whole graph in memory, and that is usually the first wall.
The per-account working set is small — one dense matrix the size of the
neighbourhood — so if the graph fits, scoring generally fits.

If the graph does not fit, build it more cheaply than networkx does. The
research repository constructs the edge set directly with pandas for exactly
this reason, which was several times faster and made a 176-million-edge graph
possible at all.

## Measuring before optimising

Neighbourhood sizes are cheap to check, and they tell you immediately whether
you have a tail problem:

```python
import pandas as pd

degrees = pd.Series(dict(graph.degree()))
print(degrees.describe())
print(degrees.nlargest(10))
```

If the top of that list is orders of magnitude above the median, hub removal
will do more for you than anything else on this page.
