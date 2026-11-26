"""Procedural green surfaces built by summing simple terrain layers.

Each layer factory returns a function ``f(X, Y) -> Z``. Pass layers to
:func:`build` to sample their sum on a grid::

    green = build(30, 25, 0.05, [tilt(1.5, 270), tier(0.25, (15, 14), 90, 2.5)])

Directions are azimuths in degrees counter-clockwise from +x.
"""

from __future__ import annotations

from typing import Callable, Sequence

import numpy as np
from scipy import ndimage

from greensim.terrain.boundary import GreenBoundary
from greensim.terrain.heightfield import HeightField

Layer = Callable[[np.ndarray, np.ndarray], np.ndarray]


def _unit(deg: float) -> tuple[float, float]:
    r = np.radians(deg)
    return float(np.cos(r)), float(np.sin(r))


def tilt(slope_pct: float, downhill_deg: float) -> Layer:
    """Uniform plane falling at ``slope_pct`` toward ``downhill_deg``."""
    ux, uy = _unit(downhill_deg)

    def f(X, Y):
        return -(slope_pct / 100.0) * (X * ux + Y * uy)

    return f


def tier(height: float, through: tuple[float, float], uphill_deg: float, width: float) -> Layer:
    """Smooth step of ``height`` m across a line through ``through``.

    The upper level lies toward ``uphill_deg``. The bank is roughly ``width`` m
    wide; its steepest slope is ``height / width``.
    """
    ux, uy = _unit(uphill_deg)
    px, py = through

    def f(X, Y):
        d = (X - px) * ux + (Y - py) * uy
        return 0.5 * height * (1.0 + np.tanh(2.0 * d / width))

    return f


def mound(center: tuple[float, float], height: float, radius: float) -> Layer:
    """Gaussian bump (negative ``height`` makes a hollow). ``radius`` is about 2 sigma."""
    cx, cy = center
    sigma = radius / 2.0

    def f(X, Y):
        return height * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * sigma**2))

    return f


def ridge(start: tuple[float, float], end: tuple[float, float], height: float, width: float) -> Layer:
    """Gaussian spine along the segment start-end. ``width`` is about 2 sigma across."""
    a = np.asarray(start, dtype=float)
    b = np.asarray(end, dtype=float)
    ab = b - a
    sigma = width / 2.0

    def f(X, Y):
        t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / ab.dot(ab), 0.0, 1.0)
        dx = X - (a[0] + t * ab[0])
        dy = Y - (a[1] + t * ab[1])
        return height * np.exp(-(dx**2 + dy**2) / (2 * sigma**2))

    return f


def noise(amplitude: float, wavelength: float, seed: int | None = None) -> Layer:
    """Smooth random undulation with standard deviation ``amplitude`` m.

    White noise is smoothed with a Gaussian of sigma = ``wavelength / (2*pi)``.
    Larger values give broader, gentler swells. The typical slope it adds is about
    ``amplitude / (0.16 * wavelength)``, so 0.02 m over 25 m adds about 0.5 %. Real
    greens have broad swells; short wavelengths (under about 10 m) look like ripples.
    The grid spacing is read from the X samples, so the same layer works at any resolution.
    """

    def f(X, Y):
        rng = np.random.default_rng(seed)
        spacing = float(X[0, 1] - X[0, 0])
        sigma_cells = wavelength / (2 * np.pi * spacing)
        field = ndimage.gaussian_filter(rng.standard_normal(X.shape), sigma_cells, mode="reflect")
        return amplitude * field / max(field.std(), 1e-12)

    return f


def build(
    width: float,
    length: float,
    spacing: float,
    layers: Sequence[Layer],
    origin: tuple[float, float] = (0.0, 0.0),
) -> HeightField:
    """Sample the sum of ``layers`` on a grid."""

    def total(X, Y):
        z = np.zeros_like(X)
        for layer in layers:
            z = z + layer(X, Y)
        return z

    return HeightField.from_function(total, width, length, spacing, origin)


def sample_green(seed: int = 0, spacing: float = 0.05) -> tuple[HeightField, GreenBoundary]:
    """A typical ~500 m^2 green with a back tier, front-to-back tilt and a side mound.

    Tuned to the slope guidelines in docs/golf-green-standards.md. Flat areas sit at
    about 1-3 %. Only the tier bank goes above about 5 %, peaking near 6.6 %, so a ball
    still holds there at stimp 11 and below.

    The grid is 36 x 30 m. The putting surface is centred at (18, 15) and the
    area outside the boundary stands in for fringe/surrounds. +y is "back".
    """
    boundary = GreenBoundary.organic(18.0, 15.0, 14.0, 11.5, irregularity=0.12, seed=seed)
    field = build(
        36.0,
        30.0,
        spacing,
        [
            tilt(1.5, 270.0),  # drains toward the front (-y)
            tier(0.25, (18.0, 18.5), 100.0, 5.0),  # back tier, bank peaks ~5 %
            mound((26.0, 10.0), 0.15, 7.0),  # right-front shoulder, <= ~2.6 %
            noise(0.02, 25.0, seed=seed),  # broad swells, ~0.5 % typical
        ],
    )
    return field, boundary
