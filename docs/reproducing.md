# Reproducing the paper

The experiments, baselines, figures and tables live in a separate repository:
**[B-Deprez/GARG-AML](https://github.com/B-Deprez/GARG-AML)**.

This package holds the method. The research repository holds everything that
surrounds it — dataset loaders for the IBM AMLworld data, label construction,
the evaluation grid, the FlowScope, AutoAudit and GraphSAGE baselines, and the
notebooks producing the figures.

## Matching a published run

- **Preprocessing:** Louvain, `resolution=10`, `seed=1997`, intra-community
  edges only — `ga.reduce_graph(graph)` with its defaults.
- **Score type:** `weighted_average`, the package default.
- **Direction:** the paper reports both.

## Two things this package does not reproduce

**The synthetic datasets.** `smurfing_graph` is a networkx reimplementation for
documentation and tests. The paper's 66 synthetic datasets were generated with
python-igraph under its own RNG and are not reproduced bit for bit. Use the
research repository's generator. See
[decision 0005](decisions/0005-synthetic-generator-differs.md).

**The transpose-max directed variant.** The pre-extraction code contained a
`max(score, transposed_score)` step with no counterpart in the paper, reachable
only through a function no experiment called. It is not ported. See
[decision 0007](decisions/0007-directed-score-is-equation-14.md).

## Version pinning

Pin an exact version when reproducing published numbers:

```bash
pip install garg-aml==0.1.0
```

Each release is tagged in the repository and archived with a DOI, so a paper can
cite the exact code that produced its results.
