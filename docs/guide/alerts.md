# Turning scores into alerts

A score per account is not an alert list. Two decisions turn one into the other,
and both are yours.

## Threshold or top-K?

**Top-K** — take the K highest-scoring accounts — matches how alerting actually
works: a team can review a fixed number of cases per day, and K is that number.
It is also what the evaluation metrics in the paper are built around.

**A fixed threshold** — everything above 0.7, say — is tempting but brittle. The
score distribution shifts with the graph, the preprocessing and the period, so
a threshold tuned in March is a different alert volume in June.

Start with top-K sized to your review capacity. Read
[the note on ties](interpreting.md#ties) first — at the top of the distribution
they are common enough to make a naive top-K partly arbitrary.

## The imbalance

Laundering labels are extremely rare: **under 0.1%** of accounts in the paper's
datasets. Three consequences worth internalising before reading any metric:

- **Accuracy is meaningless.** Flagging nothing scores over 99.9%.
- **A "low" precision may be excellent.** At a 0.1% base rate, precision of 5%
  is a fifty-fold lift over random review.
- **AUC-ROC flatters everything.** With this much imbalance it is dominated by
  the easy negatives. Prefer precision@K, recall@K, and average precision.

## Measuring

If you have labels, measure at the K you will actually use:

```python
scores = ga.score(graph)["GARGAML"]
ranked = scores.sort_values(ascending=False, kind="stable")

k = 100
flagged = ranked.head(k).index
hits = int(labels.reindex(flagged).sum())

print(f"precision@{k}: {hits / k:.1%}")
print(f"recall@{k}:    {hits / labels.sum():.1%}")
print(f"lift@{k}:      {(hits / k) / labels.mean():.1f}x")
```

Lift is the honest headline: how much better than reviewing accounts at random.

## Using it alongside what you have

GARG-AML is a structural signal, not a complete system. It is at its most useful
as one feature among several, not as a standalone alert generator — a high score
plus an unusual amount profile is far more actionable than either alone. See
[using scores as features](features.md).

The paper positions it the same way: the score is strong on its own, and
stronger when a model combines it with neighbourhood statistics.
