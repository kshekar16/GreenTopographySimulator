"""Outline of the putting surface as a closed polygon."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib.path import Path as MplPath
from scipy import ndimage

from greensim.terrain.heightfield import HeightField


@dataclass(eq=False)
class GreenBoundary:
    """Closed polygon (vertices in order; the last vertex joins back to the first)."""

    vertices: np.ndarray

    def __post_init__(self) -> None:
        self.vertices = np.asarray(self.vertices, dtype=float)
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 2 or len(self.vertices) < 3:
            raise ValueError("vertices must have shape (N, 2) with N >= 3")
        self._path = MplPath(self.vertices, closed=False)
        self._mask_cache: tuple[HeightField, np.ndarray] | None = None

    # --- factories ------------------------------------------------------
    @classmethod
    def ellipse(cls, cx: float, cy: float, a: float, b: float, rotation_deg: float = 0.0, n: int = 128) -> GreenBoundary:
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        r = np.radians(rotation_deg)
        x, y = a * np.cos(t), b * np.sin(t)
        return cls(np.column_stack([cx + x * np.cos(r) - y * np.sin(r), cy + x * np.sin(r) + y * np.cos(r)]))

    @classmethod
    def organic(
        cls,
        cx: float,
        cy: float,
        a: float,
        b: float,
        irregularity: float = 0.12,
        harmonics: int = 4,
        seed: int | None = None,
        n: int = 180,
    ) -> GreenBoundary:
        """Ellipse with smooth random bulges and bays, like a real green outline."""
        rng = np.random.default_rng(seed)
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        wobble = np.zeros_like(t)
        for k in range(2, 2 + harmonics):
            wobble += rng.normal(0, 1) / k * np.cos(k * t + rng.uniform(0, 2 * np.pi))
        wobble *= irregularity / max(np.abs(wobble).max(), 1e-12)
        scale = 1.0 + wobble
        return cls(np.column_stack([cx + a * scale * np.cos(t), cy + b * scale * np.sin(t)]))

    # --- queries --------------------------------------------------------
    @property
    def area(self) -> float:
        x, y = self.vertices[:, 0], self.vertices[:, 1]
        return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

    def contains(self, x, y) -> np.ndarray:
        """Point-in-polygon test, vectorised over points."""
        x, y = np.broadcast_arrays(np.asarray(x, dtype=float), np.asarray(y, dtype=float))
        pts = np.column_stack([x.ravel(), y.ravel()])
        return self._path.contains_points(pts).reshape(x.shape)

    def mask(self, field: HeightField) -> np.ndarray:
        """Boolean grid (same shape as ``field.z``): True where the node is on the green.

        Cached for the most recent field, so repeated putts on one green don't recompute it.
        """
        cached = self._mask_cache
        if cached is not None and cached[0] is field:
            return cached[1]
        X, Y = field.meshgrid()
        m = self.contains(X, Y)
        m.flags.writeable = False
        self._mask_cache = (field, m)
        return m

    def edge_distance_grid(self, field: HeightField) -> np.ndarray:
        """Distance (m) from each on-green node to the nearest off-green node; 0 off the green.

        Grid-based (exact Euclidean distance transform), accurate to about one cell.
        """
        inside = self.mask(field)
        return ndimage.distance_transform_edt(inside) * field.spacing
