# Installation

```bash
pip install garg-aml
```

Python 3.10 or newer. The core depends only on numpy, pandas, networkx and
scipy — no deep-learning stack, nothing that needs compiling.

## Optional extras

| Extra | Install | What it adds |
|---|---|---|
| `progress` | `pip install 'garg-aml[progress]'` | `progress=True` progress bars (tqdm) |
| `parallel` | `pip install 'garg-aml[parallel]'` | `n_jobs` other than 1 (joblib) |
| `sklearn` | `pip install 'garg-aml[sklearn]'` | the `GargAmlScorer` estimator |

Ask for several at once with `pip install 'garg-aml[progress,parallel]'`.

Each is genuinely optional: the package imports and scores without any of them,
and reaching for a feature you have not installed raises an error that names the
extra to install.

## Verifying

```python
import garg_aml as ga

graph, labels = ga.smurfing_graph(n_nodes=100, n_patterns=2, seed=1)
print(ga.score(graph).head())
```

If that prints a table of scores, you are set. See the
[quickstart](quickstart.md) for what to do with them.
