"""
GARG-AML: graph-based detection of smurfing patterns in transaction networks.

Smurfing moves money from one account to another through intermediate mules, so
that source and target never transact directly. In the second-order
neighbourhood of such a node the adjacency matrix splits into blocks whose
on-diagonal parts are empty and whose off-diagonal parts are dense. GARG-AML
scores every node by exactly that contrast, in [-1, 1], with higher meaning more
smurfing-like.

References
----------
Deprez, B., Baesens, B., Verdonck, T., & Verbeke, W. (2025). GARG-AML against
Smurfing: A Scalable and Interpretable Graph-Based Framework for Anti-Money
Laundering. arXiv:2506.04292.
"""

import logging

__version__ = "0.1.0.dev0"

# A library attaches no handlers of its own; the application decides.
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Populated in Phase 4. Anything absent here is private and unstable.
__all__: list[str] = []
