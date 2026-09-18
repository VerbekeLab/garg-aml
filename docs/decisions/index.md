# Design decisions

One short record per non-obvious choice: what was decided, why, and what breaks
if it is reversed. These exist so that a maintainer who did not write the code —
or the paper — can tell a deliberate convention from a bug.

Several of them freeze behaviour that *looks* wrong. It is not: those exact
values produced the results published in
[arXiv:2506.04292](https://arxiv.org/abs/2506.04292).

| | |
|---|---|
| [0001](0001-weighted-average-default.md) | `weighted_average` is the default score type |
| [0002](0002-louvain-is-explicit.md) | Louvain reduction is a separate, opt-in step |
| [0003](0003-frozen-edge-cases.md) | Three degenerate cases return fixed values |
| [0004](0004-two-stage-pipeline.md) | Scoring is two-stage, and there is only one implementation |
| [0005](0005-synthetic-generator-differs.md) | The synthetic generator does not reproduce the paper's datasets |
| [0006](0006-no-torch-dependency.md) | No PyTorch, ever |
| [0007](0007-directed-score-is-equation-14.md) | The directed score is Eq. 14, without the transpose-max |
