# 0001 — `weighted_average` is the default score type

**Decision.** `score(...)` defaults to `score_type="weighted_average"`.

**Context.** Two aggregations exist. `basic` takes an unweighted mean over the
penalty blocks; `weighted_average` weights each block by its number of free
entries — the `l1`, `l3` sizes of Eq. 8 and their directed analogues. The
pre-extraction code defaulted to `basic`, but every experiment in the paper
passed `weighted_average` explicitly.

**Why.** A default that no published result uses is a trap. Weighting by block
size is also the better estimator: an unweighted mean lets a two-entry block
count as much as a two-hundred-entry one.

**Consequence.** Anyone porting code that relied on the old default gets
different numbers. This is called out in the changelog and the migration notes;
`score_type="basic"` remains available.
