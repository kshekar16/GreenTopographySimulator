"""2D plan views (matplotlib): slope heatmap, contours, pin areas and putts."""

from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

from greensim.physics.ball import PuttResult
from greensim.physics.hole import Hole
from greensim.terrain.boundary import GreenBoundary
from greensim.terrain.heightfield import HeightField


def plot_green(
    field: HeightField,
    boundary: GreenBoundary | None = None,
    pin_mask: np.ndarray | None = None,
    putts: Sequence[PuttResult] = (),
    hole: Hole | None = None,
    contour_interval: float = 0.02,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Slope heatmap (percent) with elevation contours every ``contour_interval`` m."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 8))
    xmin, xmax, ymin, ymax = field.extent
    slope = field.slope_percent()
    if boundary is not None:
        slope = np.where(boundary.mask(field), slope, np.nan)
    im = ax.imshow(slope, origin="lower", extent=field.extent, cmap="viridis", vmin=0, vmax=6)
    plt.colorbar(im, ax=ax, label="Slope (%)", shrink=0.8)

    X, Y = field.meshgrid()
    levels = np.arange(np.floor(field.z.min() / contour_interval), np.ceil(field.z.max() / contour_interval) + 1) * contour_interval
    ax.contour(X, Y, field.z, levels=levels, colors="k", linewidths=0.4, alpha=0.5)

    if pin_mask is not None and pin_mask.any():
        ax.contourf(X, Y, pin_mask.astype(float), levels=[0.5, 1.5], colors="none", hatches=["//"])
        ax.contour(X, Y, pin_mask.astype(float), levels=[0.5], colors="white", linewidths=1)
    if boundary is not None:
        v = np.vstack([boundary.vertices, boundary.vertices[:1]])
        ax.plot(v[:, 0], v[:, 1], "w-", lw=2)
    for putt in putts:
        color = {"holed": "gold", "stopped": "white"}.get(putt.outcome, "orangered")
        ax.plot(putt.path[:, 0], putt.path[:, 1], "-", color=color, lw=1.5)
        ax.plot(*putt.path[0], "o", color=color, ms=4)
    if hole is not None:
        ax.add_patch(plt.Circle((hole.x, hole.y), max(hole.radius, 0.15), color="red", zorder=5))

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Slope, contours" + (", valid pin areas (hatched)" if pin_mask is not None else ""))
    return ax
