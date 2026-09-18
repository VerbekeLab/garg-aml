"""
Block densities of a second-order ego graph's adjacency matrix.

Each function takes the ordered adjacency matrix and the block sizes, and
returns the block's density over its *free* entries together with the count of
those entries. Structurally fixed entries -- the diagonal, the ego node's own
row and column -- are excluded from both, which is why the returned size is
often smaller than the block.

Three blocks for the undirected analysis (paper section 3.2) and nine for the
directed one (section 3.3). The fallback values in the empty-block branches are
frozen behaviour: see docs/decisions/0003.
"""

import numpy as np


def _block_1(dim_1: list[int], adjacency: np.ndarray) -> tuple[float, int]:
    """Density among the ego node and its second-order neighbours."""
    block = adjacency[: dim_1[0], : dim_1[1]]
    free = block.size - (3 * dim_1[0]) + 2

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_2(
    dim_1: list[int], dim_2: list[int], adjacency: np.ndarray
) -> tuple[float, int]:
    """Density between first-order and second-order neighbours."""
    block = adjacency[dim_1[0] : dim_1[0] + dim_2[0], : dim_2[1]]
    # The ego node's own edge to each first-order neighbour is structural.
    total = block.sum() - dim_2[0]
    free = block.size - dim_2[0]

    if free > 0:
        density = total / free
    else:
        density = 1

    return density, free


def _block_3(
    dim_1: list[int], dim_2: list[int], dim_3: list[int], adjacency: np.ndarray
) -> tuple[float, int]:
    """Density among the first-order neighbours."""
    block = adjacency[dim_1[0] :, dim_2[1] :]
    free = block.size - dim_3[0]

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_00(adjacency: np.ndarray, size_0: int) -> tuple[float, int]:
    """Density among level-0 nodes (senders)."""
    block = adjacency[:size_0, :size_0]
    free = block.size - (3 * size_0) + 2

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_01(adjacency: np.ndarray, size_0: int, size_1: int) -> tuple[float, int]:
    """Density from level 0 (senders) to level 1 (mules)."""
    block = adjacency[:size_0, size_0 : size_0 + size_1]
    free = block.size

    if free > 0:
        density = block.sum() / free
    else:
        density = 1  # Block holds only sure connections => treat as full

    return density, free


def _block_02(
    adjacency: np.ndarray, size_0: int, size_1: int, size_2: int
) -> tuple[float, int]:
    """Density from level 0 (senders) to level 2 (receivers)."""
    block = adjacency[:size_0, size_0 + size_1 :]
    free = block.size - size_2

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_10(adjacency: np.ndarray, size_0: int, size_1: int) -> tuple[float, int]:
    """Density from level 1 (mules) back to level 0 (senders)."""
    block = adjacency[size_0 : size_0 + size_1, :size_0]
    free = block.size

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_11(adjacency: np.ndarray, size_0: int, size_1: int) -> tuple[float, int]:
    """Density among level-1 nodes (mules)."""
    block = adjacency[size_0 : size_0 + size_1, size_0 : size_0 + size_1]
    free = block.size - size_1

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_12(
    adjacency: np.ndarray, size_0: int, size_1: int, size_2: int
) -> tuple[float, int]:
    """Density from level 1 (mules) to level 2 (receivers)."""
    block = adjacency[size_0 : size_0 + size_1, size_0 + size_1 :]
    free = block.size

    if free > 0:
        density = block.sum() / free
    elif size_2 > 0:
        density = 1  # Block holds only sure connections => treat as full
    else:
        density = 0  # No connections at all

    return density, free


def _block_20(
    adjacency: np.ndarray, size_0: int, size_1: int, size_2: int
) -> tuple[float, int]:
    """Density from level 2 (receivers) back to level 0 (senders)."""
    block = adjacency[size_0 + size_1 :, :size_0]
    free = block.size - size_2

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_21(adjacency: np.ndarray, size_0: int, size_1: int) -> tuple[float, int]:
    """Density from level 2 (receivers) back to level 1 (mules)."""
    block = adjacency[size_0 + size_1 :, size_0 : size_0 + size_1]
    free = block.size

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free


def _block_22(
    adjacency: np.ndarray, size_0: int, size_1: int, size_2: int
) -> tuple[float, int]:
    """Density among level-2 nodes (receivers)."""
    block = adjacency[size_0 + size_1 :, size_0 + size_1 :]
    free = block.size - size_2

    if free > 0:
        density = block.sum() / free
    else:
        density = 0

    return density, free
