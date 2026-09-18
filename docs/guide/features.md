# Using scores as features

The score is one number per account. The paper's stronger results come from
feeding it, plus a summary of the neighbourhood around it, into an ordinary
classifier.

## The feature table

```python
scores = ga.score(graph)
features = ga.build_features(graph, scores)
```

Ten columns:

| Column | Meaning |
|---|---|
| `GARGAML` | the account's own score |
| `GARGAML_min/mean/max/std` | the same over its direct counterparties |
| `degree` | its number of counterparties |
| `degree_min/mean/max/std` | the same over its counterparties |

The neighbourhood statistics are what let a model distinguish an account that is
*in* a pattern from one that merely *touches* one. A mule sits among other
high-scoring accounts; a legitimate business that happens to pay one mule does
not.

!!! warning "Use the same graph"
    Pass `build_features` the graph the scores were computed on. If you scored a
    reduced graph, the degrees must come from the reduced graph too, or the
    features describe two different networks.

## With scikit-learn

```python
from garg_aml import GargAmlScorer

features = GargAmlScorer(reduce=True, resolution=10).fit_transform(graph)
```

Needs the `sklearn` extra. Nothing is learned — GARG-AML is closed-form, so
`fit` has no parameters to estimate. The estimator exists so the step composes
in a pipeline, not because there is a model inside it.

## A caution on evaluation

Training a classifier on these features is **transductive**: every account was
scored as part of one graph, so a train/test split on the feature table does not
separate the test accounts from the training ones structurally — they were
neighbours when the scores were computed.

That is not wrong, but it is not the same as a held-out evaluation, and a
split-on-the-feature-table number will be optimistic relative to scoring a
genuinely unseen period. Say which one you are reporting.

## Building your own

The pieces are public if the ten columns are not what you want:

```python
from garg_aml import neighbour_score_stats, neighbour_degree_stats

stats = neighbour_score_stats(graph, "account", scores["GARGAML"].to_dict())
```

And the raw block densities are available through
`ga.score(graph, return_measures=True)` if you would rather let a model see the
components than the aggregated score.
