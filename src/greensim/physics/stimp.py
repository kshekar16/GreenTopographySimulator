"""Green speed (Stimpmeter) relations.

Model: once rolling, the ball decelerates at a constant rate ``a`` on flat
ground. A Stimpmeter ball leaves the ramp at ``v0`` and rolls ``S`` feet, so
``a = v0**2 / (2 * S)``.
"""

from __future__ import annotations

from greensim.constants import FT, STIMP_LAUNCH_SPEED


def stimp_to_deceleration(stimp_ft: float, launch_speed: float = STIMP_LAUNCH_SPEED) -> float:
    """Rolling deceleration (m/s^2) on flat ground for a Stimpmeter reading in feet."""
    if stimp_ft <= 0:
        raise ValueError("stimp must be positive")
    return launch_speed**2 / (2.0 * stimp_ft * FT)


def deceleration_to_stimp(deceleration: float, launch_speed: float = STIMP_LAUNCH_SPEED) -> float:
    """Inverse of :func:`stimp_to_deceleration`; returns feet."""
    if deceleration <= 0:
        raise ValueError("deceleration must be positive")
    return launch_speed**2 / (2.0 * deceleration) / FT


def brede_speed(uphill: float, downhill: float) -> float:
    """Slope-corrected green speed from mean uphill and downhill roll distances.

    Brede (1990): ``2 * up * down / (up + down)``. Same units as the inputs.
    Valid for rolls along the fall line on a uniform slope.
    """
    if uphill <= 0 or downhill <= 0:
        raise ValueError("roll distances must be positive")
    return 2.0 * uphill * downhill / (uphill + downhill)
