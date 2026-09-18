# 0006 — No PyTorch, ever

**Decision.** Core dependencies are numpy, pandas, networkx and scipy. PyTorch
is not a dependency of this package under any extra.

**Context.** The paper compares GARG-AML against a GraphSAGE baseline, which
needs `torch` and `torch-geometric`. That baseline lives in the research
repository.

**Why.** GARG-AML computes a closed-form structural score; nothing in it learns.
A practitioner evaluating it should be able to `pip install garg-aml` and get a
handful of megabytes. Pulling a deep-learning stack behind an unrelated score
would cost adoption for no functional gain, and would make the package
unusable in the locked-down environments where compliance teams work.

**Consequence.** Baselines and comparisons belong in the research repository.
scipy is the one non-obvious core dependency, and it is not optional:
`networkx.adjacency_matrix` imports it.
