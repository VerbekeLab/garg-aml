# garg-aml

Find **smurfing** in a transaction network: one score per account, computed from
local structure, with nothing to train and no labels required.

```bash
pip install garg-aml
```

```python
import garg_aml as ga

scores = ga.score(graph)  # a networkx graph of accounts and transactions
scores.sort_values("GARGAML", ascending=False).head(20)
```

## What it looks for

Smurfing moves money from one account to another through intermediate mules, so
that the source and the target never transact directly. Order the accounts in
someone's second-order neighbourhood as *[them and their second-order
neighbours | their direct counterparties]* and the adjacency matrix falls into
blocks. For a pure smurfing pattern the on-diagonal blocks are empty — the
mules do not deal with each other — and the off-diagonal blocks are full.

GARG-AML scores that contrast, from **-1** (nothing like smurfing) to **1** (a
textbook pattern).

That is the whole method. No training, no hyperparameters to tune, and every
score traceable back to the block densities it came from — you can always answer
"why did this account come up?".

## Where to go next

| | |
|---|---|
| [Quickstart](quickstart.md) | a working example in under a minute, no data download |
| [How it works](how-it-works.md) | the block intuition, and the two equations |
| [Preparing your data](guide/data.md) | edge lists, directedness, what counts as an account |
| [Interpreting a score](guide/interpreting.md) | what 0.8 means, and what it does not |
| [Turning scores into alerts](guide/alerts.md) | thresholds, top-K, and the imbalance problem |
| [Limitations](limitations.md) | read before you rely on it |
| [API reference](reference/index.md) | every public function |

## Citing

This package implements the method described in
[arXiv:2506.04292](https://arxiv.org/abs/2506.04292). If you use it in
published work, please cite the paper — the BibTeX entry is in the
[README](https://github.com/VerbekeLab/garg-aml#citation).

The experiments, baselines and paper reproduction live in a separate repository:
[B-Deprez/GARG-AML](https://github.com/B-Deprez/GARG-AML).
