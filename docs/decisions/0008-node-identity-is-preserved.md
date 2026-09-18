# 0008 — Node identity is preserved

**Decision.** Whatever the caller's node ids are — `str`, `int`, tuple — they
come back as the index of every returned frame, unchanged.

**Context.** The pre-extraction code did not do this consistently.
`define_gargaml_scores_undirected` collected node ids with
`measures["node"].tolist()`, preserving their dtype;
`define_gargaml_scores_directed` collected them inside a `DataFrame.iterrows()`
loop, which coerces each row to a single dtype. With float measure columns in the
frame, that silently turned integer node ids into floats. The frozen fixtures
record it: `scores_directed_raw.csv` is indexed `0.0, 1.0` where
`scores_undirected_raw.csv` is indexed `0, 1`.

**Why this is not a correction to published results.** It is cosmetic. Python
hashes `0.0` and `0` identically, so the downstream dictionary and networkx
lookups resolve either way, and pandas joins a float64 index against an int64
index by value. The IBM account ids are strings in any case, so `iterrows()`
left them alone. Nothing downstream was reading a wrong number.

**Why change it.** A library that renames its caller's keys is surprising, and
node ids are the one thing a user matches results back to their own data with.
The package uses `.tolist()` on both paths.

**Consequence.** The directed score and feature fixtures carry a float index
that the package deliberately does not reproduce. Both test layers therefore
compare indices **by value** rather than by dtype, and say so inline. That is
strictly stronger than what came before: the golden comparison used to drop the
index entirely, so node alignment was never checked at all.
