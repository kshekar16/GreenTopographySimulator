"""Point cloud -> HeightField. The same path is used for simulated and real scans."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import griddata

from greensim.terrain.heightfield import HeightField


def points_to_heightfield(
    xyz: np.ndarray,
    spacing: float,
    extent: tuple[float, float, float, float] | None = None,
) -> tuple[HeightField, np.ndarray]:
    """Grid a point cloud by averaging the points in each cell.

    Empty cells are filled by linear interpolation, then nearest-neighbour
    outside the convex hull. Returns ``(field, coverage)``. ``coverage`` is the
    number of points per cell, and 0 means the cell was filled in.
    """
    xyz = np.asarray(xyz, dtype=float).reshape(-1, 3)
    if len(xyz) == 0:
        raise ValueError("point cloud is empty")
    if extent is None:
        extent = (xyz[:, 0].min(), xyz[:, 0].max(), xyz[:, 1].min(), xyz[:, 1].max())
    xmin, xmax, ymin, ymax = extent
    nx = int(round((xmax - xmin) / spacing)) + 1
    ny = int(round((ymax - ymin) / spacing)) + 1

    i = np.rint((xyz[:, 0] - xmin) / spacing).astype(int)
    j = np.rint((xyz[:, 1] - ymin) / spacing).astype(int)
    keep = (i >= 0) & (i < nx) & (j >= 0) & (j < ny)
    if not keep.any():
        raise ValueError("no points fall inside the requested extent")
    flat = j[keep] * nx + i[keep]
    count = np.bincount(flat, minlength=nx * ny)
    total = np.bincount(flat, weights=xyz[keep, 2], minlength=nx * ny)

    z = np.full(nx * ny, np.nan)
    filled = count > 0
    z[filled] = total[filled] / count[filled]
    z = z.reshape(ny, nx)
    coverage = count.reshape(ny, nx)

    if (~filled).any():
        X, Y = np.meshgrid(xmin + np.arange(nx) * spacing, ymin + np.arange(ny) * spacing)
        known = np.column_stack([X[coverage > 0], Y[coverage > 0]])
        values = z[coverage > 0]
        holes = np.isnan(z)
        z[holes] = griddata(known, values, (X[holes], Y[holes]), method="linear")
        still = np.isnan(z)
        if still.any():
            z[still] = griddata(known, values, (X[still], Y[still]), method="nearest")

    return HeightField(z, spacing, (xmin, ymin)), coverage
