# Limitations

Read this before relying on the output.

## What it cannot see

**Only structure.** Amounts, timestamps, currencies and transaction counts are
not used. Two accounts that transact once and two that transact a thousand times
are the same edge. Smurfing that is obvious from amounts — hundreds of transfers
just under a reporting threshold — is invisible here unless the *shape* is also
there.

**Only this pattern.** The method targets gather-scatter and scatter-gather
structures. Laundering that does not route through intermediaries — cash, trade
mis-invoicing, a single large transfer to a shell company — has no reason to
score high. **A low score is not evidence of legitimacy.**

**Only within the graph you supply.** A bank sees its own customers'
transactions. In the paper's own analysis, a single institution's view preserved
every first-order relationship but only about 7% of second-order ones, and more
than half its customers lost their entire second-order neighbourhood. Worse, the
loss **biases scores upward** rather than adding noise: a missing neighbourhood
empties the penalty blocks, so partial visibility produces *more* false
positives, not just worse ranking.

## Where the numbers mislead

**Ties.** Many accounts share exactly the same score, especially 1.0. A raw
top-K is partly an artefact of sort order. See
[Interpreting a score](guide/interpreting.md#ties).

**Extreme imbalance.** Under 0.1% of accounts are labelled in the reference
datasets. Accuracy and AUC-ROC are close to useless at that base rate; use
precision@K, recall@K and lift.

**Transductive evaluation.** If you train a model on
[the feature table](guide/features.md), every account was scored as part of one
graph. A train/test split on that table does not separate test accounts
structurally from training ones — they were neighbours when the scores were
computed. Such a number is optimistic relative to scoring an unseen period.

**Preprocessing changes the scale.** Scores from a reduced graph and a full
graph are not comparable. After `reduce_graph` at a high resolution, many
accounts have no neighbourhood left and score -1 — which is a statement about
the preprocessing, not about the account.

## Where the method is uncertain

**The directed score underperforms the undirected one**, which is
counter-intuitive: one-directional flow is definitional for smurfing, so the
directed variant should carry more information. Why it does not is an open
question — the level-assignment rule may be too strict, or bidirectional edges
may be over-penalised. Start with undirected.

**Labels are propensity-based.** In the reference datasets an account counts as
laundering when a share of its transactions are flagged. That cut-off is a
choice, and results move with it.

## On claims

This package implements a method that performs competitively with published
baselines on the datasets it was evaluated on, at lower computational cost.
It is not established as state of the art, and the reduction in false positives
relative to alternatives is dataset-specific rather than a general property.
Evaluate it on your own data before relying on either claim.
