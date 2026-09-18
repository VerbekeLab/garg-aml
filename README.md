# garg-aml

Graph-based detection of **smurfing** patterns in transaction networks.

Smurfing moves money from one account to another through intermediate mules, so
source and target never transact directly. In the second-order neighbourhood of
such an account the adjacency matrix splits into blocks whose on-diagonal parts
are empty and whose off-diagonal parts are dense. GARG-AML scores every account
by exactly that contrast — one number in [-1, 1], computed from local structure
alone, with no training and no labels.

[![PyPI](https://img.shields.io/pypi/v/garg-aml.svg)](https://pypi.org/project/garg-aml/)
[![Python](https://img.shields.io/pypi/pyversions/garg-aml.svg)](https://pypi.org/project/garg-aml/)
[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

## Install

```bash
pip install garg-aml
```

## Use

```python
import garg_aml as ga

graph, labels = ga.smurfing_graph(n_nodes=100, n_patterns=2, seed=1)
scores = ga.score(graph)["GARGAML"]
scores.sort_values(ascending=False, kind="stable").head(10)
```

Eight of those ten accounts are in an injected pattern, out of 13 among 109 —
with no training, no labels and no tuning.

Full documentation: <https://verbekelab.github.io/garg-aml/>

## Citation

If you use this package, please cite the paper:

```bibtex
@article{deprez2025gargaml,
  title   = {{GARG-AML} against Smurfing: A Scalable and Interpretable
             Graph-Based Framework for Anti-Money Laundering},
  author  = {Deprez, Bruno and Baesens, Bart and Verdonck, Tim and
             Verbeke, Wouter},
  journal = {arXiv preprint arXiv:2506.04292},
  year    = {2025}
}
```

## Links

- Paper: [arXiv:2506.04292](https://arxiv.org/abs/2506.04292)
- Experiments and paper reproduction: [B-Deprez/GARG-AML](https://github.com/B-Deprez/GARG-AML)
- Contributing and release process: [CONTRIBUTING.md](CONTRIBUTING.md)

## Licence

MIT — see [LICENSE](LICENSE).
