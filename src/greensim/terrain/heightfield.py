"""Regular-grid height field representing the green surface z = f(x, y)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class HeightField:
    """Surface heights on a regular grid.

    ``z[j, i]`` is the height (m) at ``x = origin[0] + i * spacing``,
    ``y = origin[1] + j * spacing``. Rows run along y, columns along x.

    Treat ``z`` as read-only after construction: the gradient grids are derived
    from it once. To change the surface, build a new HeightField.
    """

    z: np.ndarray
    spacing: float
    origin: tuple[float, float] = (0.0, 0.0)
    _gx: np.ndarray = field(init=False, repr=False)
    _gy: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.z = np.asarray(self.z, dtype=float)
        if self.z.ndim != 2 or min(self.z.shape) < 2:
            raise ValueError(f"z must be a 2D array of at least 2x2, got shape {self.z.shape}")
        if self.spacing <= 0:
            raise ValueError("spacing must be positive")
        self.origin = (float(self.origin[0]), float(self.origin[1]))
        self._gy, self._gx = np.gradient(self.z, self.spacing)

    # --- construction ---------------------------------------------------
    @classmethod
    def from_function(
        cls,
        fn: Callable[[np.ndarray, np.ndarray], np.ndarray | float],
        width: float,
        length: float,
        spacing: float,
        origin: tuple[float, float] = (0.0, 0.0),
    ) -> HeightField:
        """Sample ``fn(X, Y)`` on a grid covering ``width`` (x) by ``length`` (y) metres."""
        nx = int(round(width / spacing)) + 1
        ny = int(round(length / spacing)) + 1
        x = origin[0] + np.arange(nx) * spacing
        y = origin[1] + np.arange(ny) * spacing
        X, Y = np.meshgrid(x, y)
        z = np.broadcast_to(np.asarray(fn(X, Y), dtype=float), X.shape).copy()
        return cls(z, spacing, origin)

    # --- geometry -------------------------------------------------------
    @property
    def ny(self) -> int:
        return self.z.shape[0]

    @property
    def nx(self) -> int:
        return self.z.shape[1]

    @property
    def x(self) -> np.ndarray:
        return self.origin[0] + np.arange(self.nx) * self.spacing

    @property
    def y(self) -> np.ndarray:
        return self.origin[1] + np.arange(self.ny) * self.spacing

    @property
    def extent(self) -> tuple[float, float, float, float]:
        """(xmin, xmax, ymin, ymax)"""
        x0, y0 = self.origin
        return (x0, x0 + (self.nx - 1) * self.spacing, y0, y0 + (self.ny - 1) * self.spacing)

    def meshgrid(self) -> tuple[np.ndarray, np.ndarray]:
        return np.meshgrid(self.x, self.y)

    def contains(self, x, y) -> np.ndarray | bool:
        xmin, xmax, ymin, ymax = self.extent
        x, y = np.asarray(x), np.asarray(y)
        return (x >= xmin) & (x <= xmax) & (y >= ymin) & (y <= ymax)

    # --- sampling -------------------------------------------------------
    def _bilinear(self, grid: np.ndarray, x, y) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        fx = (x - self.origin[0]) / self.spacing
        fy = (y - self.origin[1]) / self.spacing
        i0 = np.clip(np.floor(fx).astype(int), 0, self.nx - 2)
        j0 = np.clip(np.floor(fy).astype(int), 0, self.ny - 2)
        tx = np.clip(fx - i0, 0.0, 1.0)
        ty = np.clip(fy - j0, 0.0, 1.0)
        return (
            grid[j0, i0] * (1 - tx) * (1 - ty)
            + grid[j0, i0 + 1] * tx * (1 - ty)
            + grid[j0 + 1, i0] * (1 - tx) * ty
            + grid[j0 + 1, i0 + 1] * tx * ty
        )

    def height(self, x, y):
        """Bilinearly interpolated height. Points outside the grid are clamped to the edge."""
        return self._bilinear(self.z, x, y)

    def gradient(self, x, y) -> tuple[np.ndarray, np.ndarray]:
        """(dz/dx, dz/dy) at the given points (interpolated central differences)."""
        return self._bilinear(self._gx, x, y), self._bilinear(self._gy, x, y)

    def gradient_at(self, x: float, y: float) -> tuple[float, float]:
        """Scalar fast path of :meth:`gradient` for tight simulation loops."""
        fx = (x - self.origin[0]) / self.spacing
        fy = (y - self.origin[1]) / self.spacing
        i0 = min(max(int(math.floor(fx)), 0), self.nx - 2)
        j0 = min(max(int(math.floor(fy)), 0), self.ny - 2)
        tx = min(max(fx - i0, 0.0), 1.0)
        ty = min(max(fy - j0, 0.0), 1.0)
        w00 = (1 - tx) * (1 - ty)
        w10 = tx * (1 - ty)
        w01 = (1 - tx) * ty
        w11 = tx * ty
        gx, gy = self._gx, self._gy
        return (
            float(gx[j0, i0] * w00 + gx[j0, i0 + 1] * w10 + gx[j0 + 1, i0] * w01 + gx[j0 + 1, i0 + 1] * w11),
            float(gy[j0, i0] * w00 + gy[j0, i0 + 1] * w10 + gy[j0 + 1, i0] * w01 + gy[j0 + 1, i0 + 1] * w11),
        )

    # --- derived grids --------------------------------------------------
    def slope_percent(self) -> np.ndarray:
        """Slope magnitude at every grid node, in percent (rise/run * 100)."""
        return 100.0 * np.hypot(self._gx, self._gy)

    def aspect_degrees(self) -> np.ndarray:
        """Downhill direction at every node: degrees counter-clockwise from +x."""
        return np.degrees(np.arctan2(-self._gy, -self._gx)) % 360.0
