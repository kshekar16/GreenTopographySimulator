"""Slope summaries for the putting surface."""

from __future__ import annotations

import numpy as np

from greensim.constants import GRAVITY, PIN_MAX_SLOPE_PCT, ROLLING_SPHERE_FACTOR
from greensim.physics.stimp import stimp_to_deceleration
from greensim.terrain.boundary import GreenBoundary
from greensim.terrain.heightfield import HeightField


def hold_limit_pct(stimp_ft: float) -> float:
    """Steepest slope (percent) a ball can rest on at this green speed.

    The ball holds while the slope pull (5/7)*g*sin(theta) is at most the rolling
    deceleration. At stimp 10 the limit is about 7.87 %, and at stimp 13 about 6.04 %.
    On an implausibly slow green (stimp below about 0.8 ft) the ball holds on any
    slope, and the result is ``inf``.
    """
    s = stimp_to_deceleration(stimp_ft) / (ROLLING_SPHERE_FACTOR * GRAVITY)
    if s >= 1.0:
        return float("inf")
    return float(100.0 * s / np.sqrt(1.0 - s * s))  # sin -> tan, as percent grade


def slope_stats(
    field: HeightField, boundary: GreenBoundary | None = None, stimp_ft: float | None = None
) -> dict[str, float]:
    """Slope summary (percent) over the green, or over the whole grid if no boundary.

    ``share_pinnable_slope`` is the fraction at or below the 3 % pin-area guideline.
    If ``stimp_ft`` is given, ``share_unholdable`` is the fraction too steep for a
    ball to stop on at that speed.
    """
    slope = field.slope_percent()
    values = slope[boundary.mask(field)] if boundary is not None else slope.ravel()
    stats = {
        "mean": float(values.mean()),
        "p50": float(np.percentile(values, 50)),
        "p90": float(np.percentile(values, 90)),
        "max": float(values.max()),
        "share_pinnable_slope": float((values <= PIN_MAX_SLOPE_PCT).mean()),
    }
    if stimp_ft is not None:
        stats["hold_limit"] = hold_limit_pct(stimp_ft)
        stats["share_unholdable"] = float((values > stats["hold_limit"]).mean())
    return stats
