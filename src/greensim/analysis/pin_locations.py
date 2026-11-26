"""Where a hole may be cut, following USGA course set-up guidance."""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from greensim.constants import PIN_LEVEL_RADIUS, PIN_MAX_SLOPE_PCT, PIN_MIN_EDGE_DISTANCE
from greensim.terrain.boundary import GreenBoundary
from greensim.terrain.heightfield import HeightField


def valid_pin_mask(
    field: HeightField,
    boundary: GreenBoundary,
    max_slope_pct: float = PIN_MAX_SLOPE_PCT,
    level_radius: float = PIN_LEVEL_RADIUS,
    min_edge_distance: float = PIN_MIN_EDGE_DISTANCE,
) -> np.ndarray:
    """Boolean grid: True where every slope within ``level_radius`` is at most
    ``max_slope_pct`` and the node is at least ``min_edge_distance`` inside the green.
    """
    r = int(np.ceil(level_radius / field.spacing))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    disc = (xx**2 + yy**2) <= r**2
    worst_nearby = ndimage.maximum_filter(field.slope_percent(), footprint=disc, mode="nearest")
    return (boundary.edge_distance_grid(field) >= min_edge_distance) & (worst_nearby <= max_slope_pct)
