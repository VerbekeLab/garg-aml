"""
Block densities of a second-order ego graph's adjacency matrix.

Each function takes the ordered adjacency matrix and the block sizes, and
returns the block's density over its *free* entries together with the count of
those entries. Entries that are structurally fixed -- the diagonal, the ego
node's own row and column -- are excluded from both, which is why the returned
size is often smaller than the block.

Three functions for the undirected analysis (paper section 3.2) and nine for the
directed one (section 3.3). Copied unchanged from the research repository; the
degenerate-case constants are deliberate, see docs/decisions/0003.
"""


def measure_1_function(piece_1_dim, adj_full):
    """Density among the ego node and its second-order neighbours."""
    piece_1 = adj_full[: piece_1_dim[0], : piece_1_dim[1]]
    total_sum_1 = piece_1.sum()
    total_size_1 = piece_1.size
    reduced_size_1 = total_size_1 - (3 * piece_1_dim[0]) + 2

    if reduced_size_1 > 0:
        rel_1 = total_sum_1 / reduced_size_1
    else:
        rel_1 = 0

    return rel_1, reduced_size_1


def measure_2_function(piece_1_dim, piece_2_dim, adj_full):
    """Density between first-order and second-order neighbours."""
    piece_2 = adj_full[
        piece_1_dim[0] : piece_1_dim[0] + piece_2_dim[0], : piece_2_dim[1]
    ]
    total_sum_2 = piece_2.sum()
    reduced_sum_2 = total_sum_2 - piece_2_dim[0]
    total_size_2 = piece_2.size
    reduced_size_2 = total_size_2 - piece_2_dim[0]

    if reduced_size_2 > 0:
        rel_2 = reduced_sum_2 / reduced_size_2
    else:
        rel_2 = 1

    return rel_2, reduced_size_2


def measure_3_function(piece_1_dim, piece_2_dim, piece_3_dim, adj_full):
    """Density among the first-order neighbours."""
    piece_3 = adj_full[piece_1_dim[0] :, piece_2_dim[1] :]
    total_sum_3 = piece_3.sum()
    total_size_3 = piece_3.size
    reduced_size_3 = total_size_3 - piece_3_dim[0]

    if reduced_size_3 > 0:
        rel_3 = total_sum_3 / reduced_size_3
    else:
        rel_3 = 0

    return rel_3, reduced_size_3


def measure_00_function(adj_full, size_0):
    """Density among level-0 nodes (senders)."""
    piece_00 = adj_full[:size_0, :size_0]
    total_sum_00 = piece_00.sum()
    total_size_00 = piece_00.size
    reduced_size_00 = total_size_00 - (3 * size_0) + 2

    if reduced_size_00 > 0:
        rel_00 = total_sum_00 / reduced_size_00
    else:
        rel_00 = 0

    return rel_00, reduced_size_00


def measure_01_function(adj_full, size_0, size_1):
    """Density from level 0 (senders) to level 1 (mules)."""
    piece_01 = adj_full[:size_0, size_0 : size_0 + size_1]
    total_sum_01 = piece_01.sum()
    total_size_01 = piece_01.size

    if total_size_01 > 0:
        rel_01 = total_sum_01 / total_size_01
    else:
        rel_01 = 1  # Since block only contains sure connections => full sum

    return rel_01, total_size_01


def measure_02_function(adj_full, size_0, size_1, size_2):
    """Density from level 0 (senders) to level 2 (receivers)."""
    piece_02 = adj_full[:size_0, size_0 + size_1 :]
    total_sum_02 = piece_02.sum()
    total_size_02 = piece_02.size
    reduced_size_02 = total_size_02 - size_2

    if reduced_size_02 > 0:
        rel_02 = total_sum_02 / reduced_size_02
    else:
        rel_02 = 0

    return rel_02, reduced_size_02


def measure_10_function(adj_full, size_0, size_1):
    """Density from level 1 (mules) back to level 0 (senders)."""
    piece_10 = adj_full[size_0 : size_0 + size_1, :size_0]
    total_sum_10 = piece_10.sum()
    total_size_10 = piece_10.size

    if total_size_10 > 0:
        rel_10 = total_sum_10 / total_size_10
    else:
        rel_10 = 0

    return rel_10, total_size_10


def measure_11_function(adj_full, size_0, size_1):
    """Density among level-1 nodes (mules)."""
    piece_11 = adj_full[size_0 : size_0 + size_1, size_0 : size_0 + size_1]
    total_sum_11 = piece_11.sum()
    total_size_11 = piece_11.size
    reduced_size_11 = total_size_11 - size_1

    if reduced_size_11 > 0:
        rel_11 = total_sum_11 / reduced_size_11
    else:
        rel_11 = 0

    return rel_11, reduced_size_11


def measure_12_function(adj_full, size_0, size_1, size_2):
    """Density from level 1 (mules) to level 2 (receivers)."""
    piece_12 = adj_full[size_0 : size_0 + size_1, size_0 + size_1 :]
    total_sum_12 = piece_12.sum()
    total_size_12 = piece_12.size

    if total_size_12 > 0:
        rel_12 = total_sum_12 / total_size_12
    elif size_2 > 0:
        rel_12 = 1  # Since block only contains sure connections => full sum
    else:
        rel_12 = 0  # No connections at all

    return rel_12, total_size_12


def measure_20_function(adj_full, size_0, size_1, size_2):
    """Density from level 2 (receivers) back to level 0 (senders)."""
    piece_20 = adj_full[size_0 + size_1 :, :size_0]
    total_sum_20 = piece_20.sum()
    total_size_20 = piece_20.size
    reduced_size_20 = total_size_20 - size_2

    if reduced_size_20 > 0:
        rel_20 = total_sum_20 / reduced_size_20
    else:
        rel_20 = 0

    return rel_20, reduced_size_20


def measure_21_function(adj_full, size_0, size_1):
    """Density from level 2 (receivers) back to level 1 (mules)."""
    piece_21 = adj_full[size_0 + size_1 :, size_0 : size_0 + size_1]
    total_sum_21 = piece_21.sum()
    total_size_21 = piece_21.size

    if total_size_21 > 0:
        rel_21 = total_sum_21 / total_size_21
    else:
        rel_21 = 0

    return rel_21, total_size_21


def measure_22_function(adj_full, size_0, size_1, size_2):
    """Density among level-2 nodes (receivers)."""
    piece_22 = adj_full[size_0 + size_1 :, size_0 + size_1 :]
    total_sum_22 = piece_22.sum()
    total_size_22 = piece_22.size
    reduced_size_22 = total_size_22 - size_2

    if reduced_size_22 > 0:
        rel_22 = total_sum_22 / reduced_size_22
    else:
        rel_22 = 0

    return rel_22, reduced_size_22
