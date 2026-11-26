"""Simulated LIDAR scans of a height field.

Two scanner types:

* :func:`aerial_scan`: a drone or airborne sweep. Points are spread evenly over
  the area and there is no occlusion.
* :func:`terrestrial_scan`: a tripod scanner. It casts rays in an
  azimuth/elevation grid and finds where each ray first meets the surface. This
  gives the real-world look: dense rings near the tripod, sparse coverage far
  away, and shadows behind crests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from greensim.terrain.heightfield import HeightField


@dataclass(eq=False)
class PointCloud:
    xyz: np.ndarray  # (N, 3) metres
    intensity: np.ndarray  # (N,) in [0, 1]
    source_id: np.ndarray = field(default=None)  # (N,) scanner index, or None

    def __post_init__(self) -> None:
        self.xyz = np.asarray(self.xyz, dtype=float).reshape(-1, 3)
        self.intensity = np.asarray(self.intensity, dtype=float).reshape(-1)
        if self.source_id is None:
            self.source_id = np.zeros(len(self.xyz), dtype=np.uint16)
        if not (len(self.xyz) == len(self.intensity) == len(self.source_id)):
            raise ValueError("xyz, intensity and source_id must have the same length")

    def __len__(self) -> int:
        return len(self.xyz)

    @classmethod
    def concatenate(cls, clouds: Sequence["PointCloud"]) -> "PointCloud":
        return cls(
            np.vstack([c.xyz for c in clouds]),
            np.concatenate([c.intensity for c in clouds]),
            np.concatenate([c.source_id for c in clouds]),
        )


def _surface_normal_cos(field: HeightField, x, y, direction: np.ndarray) -> np.ndarray:
    """|cos| of the angle between each ray direction and the local surface normal."""
    gx, gy = field.gradient(x, y)
    n = np.column_stack([-gx, -gy, np.ones_like(gx)])
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return np.abs(np.einsum("ij,ij->i", n, direction))


def aerial_scan(
    field: HeightField,
    density: float = 400.0,
    noise_sigma: float = 0.005,
    seed: int | None = None,
) -> PointCloud:
    """Evenly distributed returns, ``density`` points per m^2, vertical noise ``noise_sigma`` m."""
    rng = np.random.default_rng(seed)
    xmin, xmax, ymin, ymax = field.extent
    n = int(density * (xmax - xmin) * (ymax - ymin))
    x = rng.uniform(xmin, xmax, n)
    y = rng.uniform(ymin, ymax, n)
    z = field.height(x, y) + rng.normal(0.0, noise_sigma, n)
    down = np.tile([0.0, 0.0, -1.0], (n, 1))
    intensity = np.clip(_surface_normal_cos(field, x, y, down) + rng.normal(0, 0.02, n), 0, 1)
    return PointCloud(np.column_stack([x, y, z]), intensity)


def terrestrial_scan(
    field: HeightField,
    position: tuple[float, float],
    instrument_height: float = 1.6,
    azimuth_step_deg: float = 0.25,
    elevation_range_deg: tuple[float, float] = (-45.0, -2.0),
    elevation_step_deg: float = 0.25,
    max_range: float = 60.0,
    range_noise_sigma: float = 0.003,
    march_steps: int = 64,
    seed: int | None = None,
    source_id: int = 0,
) -> PointCloud:
    """Ray-cast scan from a tripod at ``position``, ``instrument_height`` m above the ground."""
    if elevation_range_deg[1] >= 0.0 or elevation_range_deg[0] > elevation_range_deg[1]:
        raise ValueError("elevation_range_deg must be (low, high) with both below 0: rays have to point down")
    rng = np.random.default_rng(seed)
    sx, sy = position
    sz = float(field.height(sx, sy)) + instrument_height
    origin = np.array([sx, sy, sz])

    az = np.radians(np.arange(0.0, 360.0, azimuth_step_deg))
    el = np.radians(np.arange(elevation_range_deg[0], elevation_range_deg[1] + 1e-9, elevation_step_deg))
    AZ, EL = np.meshgrid(az, el)
    d = np.column_stack([(np.cos(EL) * np.cos(AZ)).ravel(), (np.cos(EL) * np.sin(AZ)).ravel(), np.sin(EL).ravel()])

    # The ray can only meet the surface while its height lies between the
    # surface's min and max, so the search is limited to that stretch of ray.
    zmin, zmax = float(field.z.min()), float(field.z.max())
    dz = d[:, 2]  # all negative
    t_lo = np.clip((sz - zmax) / -dz, 0.0, max_range)
    t_hi = np.clip((sz - zmin) / -dz, 0.0, max_range)

    def above(t):  # ray height minus surface height
        p = origin + t[:, None] * d
        return p[:, 2] - field.height(p[:, 0], p[:, 1])

    # Coarse march for the first sign change (handles occlusion), then bisect.
    hit = np.zeros(len(d), dtype=bool)
    a = t_lo.copy()
    b = t_hi.copy()
    prev_t = t_lo.copy()
    for k in range(1, march_steps + 1):
        t = t_lo + (t_hi - t_lo) * k / march_steps
        crossed = ~hit & (above(t) <= 0.0)
        a[crossed] = prev_t[crossed]
        b[crossed] = t[crossed]
        hit |= crossed
        prev_t = t
    a, b, d = a[hit], b[hit], d[hit]
    for _ in range(30):
        m = 0.5 * (a + b)
        p = origin + m[:, None] * d
        is_above = p[:, 2] - field.height(p[:, 0], p[:, 1]) > 0.0
        a = np.where(is_above, m, a)
        b = np.where(is_above, b, m)
    t_hit = 0.5 * (a + b)

    pts = origin + (t_hit + rng.normal(0.0, range_noise_sigma, len(t_hit)))[:, None] * d
    inside = field.contains(pts[:, 0], pts[:, 1])
    pts, d, t_hit = pts[inside], d[inside], t_hit[inside]

    cos_inc = _surface_normal_cos(field, pts[:, 0], pts[:, 1], d)
    intensity = np.clip(cos_inc * np.exp(-t_hit / 80.0) + rng.normal(0, 0.02, len(pts)), 0, 1)
    return PointCloud(pts, intensity, np.full(len(pts), source_id, dtype=np.uint16))
