# How it works

## The pattern

In a pure smurfing scheme, one account moves money to another through
intermediaries. The source pays each mule; each mule pays the target. The source
and target never transact directly, and the mules have no reason to deal with
each other.

That absence is the signal. Look at the second-order neighbourhood of the source
— itself, its direct counterparties (the mules), and everything two steps away
(the target) — and order the accounts as:

```
[ source and its second-order neighbours | its direct counterparties ]
```

The adjacency matrix then splits into blocks:

|  | source + 2nd order | 1st order |
|---|---|---|
| **source + 2nd order** | empty | full |
| **1st order** | full | empty |

The **on-diagonal** blocks are empty: the source does not pay the target, and
the mules do not pay each other. The **off-diagonal** blocks are full: everyone
in the first group deals with everyone in the second.

Ordinary banking looks nothing like this. A group of businesses that trade with
one another fills the on-diagonal blocks. A retail account with unrelated
counterparties fills neither.

## The score

GARG-AML measures each block's density over its *free* entries — excluding what
is structurally fixed, like the diagonal and the account's own edges — and takes
the contrast between the blocks that should be full and the blocks that should
be empty.

**Undirected** (paper §3.2, Eq. 8), with `block2` the off-diagonal block and
`block1`, `block3` the two on-diagonal ones:

```
score = density(block2) − weighted_mean(density(block1), density(block3))
```

weighted by the number of free entries in each block. Range **[-1, 1]**.

**Directed** (§3.3, Eq. 14). Money flowing one way is definitional for smurfing,
so the second-order neighbours split by role: **level 0** senders, **level 1**
mules, **level 2** receivers. An account two steps away sits at level 0 when no
directed path of length two reaches it in either direction. That gives a 3×3
grid of blocks, of which two should be dense:

```
score = mean(score01, score12) − mean(the other seven)
```

## Two stages

Scoring happens in two steps, and they are worth keeping apart:

```python
measures = ga.block_measures_frame(graph)  # expensive: touches the graph
scores = ga.scores_from_measures(measures)  # cheap: pure arithmetic
```

The measures are the per-account block densities and sizes. Computing them is
the whole cost; deriving a score from them is arithmetic. Persist the measures
and you can change the aggregation, compare score variants, or build features
without touching the graph again. `ga.score()` is just these two composed.

## Why it scales

Each account's score depends only on its own second-order neighbourhood. There
is no global optimisation, no matrix factorisation, and no iteration to
convergence — so accounts can be scored independently and in parallel, and
memory is bounded by the largest neighbourhood rather than by the graph. See
[Scaling](scaling.md).

## Reading further

The paper is [arXiv:2506.04292](https://arxiv.org/abs/2506.04292); §3 has the
full derivation, the structural corrections applied to each block, and worked
examples in Appendix A. This page is the intuition, not a substitute.
