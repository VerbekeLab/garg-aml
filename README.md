# garg-aml

Graph-based detection of **smurfing** patterns in transaction networks.

Smurfing moves money from one account to another through intermediate mules, so
source and target never transact directly. In the second-order neighbourhood of
such an account the adjacency matrix splits into blocks whose on-diagonal parts
are empty and whose off-diagonal parts are dense. GARG-AML scores every account
by exactly that contrast — one number in [-1, 1], computed from local structure
alone, with no training and no labels.

> **Status: pre-release.** The scoring core is being extracted from the
> [research repository](https://github.com/B-Deprez/GARG-AML). The public API
> lands in 0.1.0.

## Install

```bash
pip install garg-aml
```

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
