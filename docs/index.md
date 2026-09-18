# garg-aml

Graph-based detection of **smurfing** patterns in transaction networks.

!!! warning "Pre-release"
    The scoring core is being extracted from the
    [research repository](https://github.com/B-Deprez/GARG-AML). The public API
    and the rest of this documentation land in 0.1.0.

## What it does

Smurfing moves money from one account to another through intermediate mules, so
that source and target never transact directly. Order the nodes of an account's
second-order neighbourhood as `[account + 2nd-order neighbours | 1st-order
neighbours]` and the adjacency matrix splits into blocks: for a pure smurfing
pattern the on-diagonal blocks are empty and the off-diagonal blocks are dense.

GARG-AML scores every account by that contrast. One number in [-1, 1], computed
from local structure alone — no training, no labels, and every score traceable
back to the block densities it came from.

## Links

- Paper: [arXiv:2506.04292](https://arxiv.org/abs/2506.04292)
- [Design decisions](decisions/index.md)
- [Experiments and paper reproduction](https://github.com/B-Deprez/GARG-AML)
