"""The demo scene: a generated green, a hole, a fan of putts and a simulated scan.

Every ``greensim`` command and both viewers build their content through
:func:`build_scene`. The viewers call it again, with a new seed, when the user
asks for a new green.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from greensim.analysis import slope_stats, valid_pin_mask
from greensim.lidar import PointCloud, aerial_scan, points_to_heightfield, terrestrial_scan
from greensim.physics import Hole, PuttResult, roll_ball, stimp_to_deceleration
from greensim.physics.ball import velocity_toward
from greensim.terrain import GreenBoundary, HeightField
from greensim.terrain.generators import sample_green

SCAN_TYPES = ("terrestrial", "aerial", "none")
MAX_SEED = 99_999


class NoValidPinError(ValueError):
    """The generated green has nowhere a hole may legally be cut."""


@dataclass
class Scene:
    field: HeightField
    boundary: GreenBoundary
    hole: Hole
    putts: list[PuttResult] = field(default_factory=list)
    cloud: PointCloud | None = None
    seed: int = 0
    stimp: float = 10.0
    summary: list[str] = field(default_factory=list)


def random_seed() -> int:
    return random.randint(0, MAX_SEED)


def build_scene(
    seed: int = 0,
    stimp: float = 10.0,
    scan: str = "terrestrial",
    verbose: bool = True,
    log: Callable[[str], None] | None = None,
) -> Scene:
    """Generate the sample green for ``seed``, place a hole, roll putts and (optionally) scan it.

    Each summary line is passed to ``log`` (``print`` when ``verbose``) and also
    kept in ``Scene.summary``. Raises :class:`NoValidPinError` if no hole location
    on the green meets the guidelines.
    """
    if scan not in SCAN_TYPES:
        raise ValueError(f"scan must be one of {SCAN_TYPES}, got {scan!r}")
    if stimp <= 0:
        raise ValueError("stimp must be positive")
    sink = log if log is not None else (print if verbose else None)
    summary: list[str] = []

    def emit(line: str) -> None:
        summary.append(line)
        if sink is not None:
            sink(line)

    field_, boundary = sample_green(seed=seed)
    stats = slope_stats(field_, boundary, stimp)
    emit(
        f"Green #{seed}: {boundary.area:.0f} m^2, slope mean {stats['mean']:.1f}%, p90 {stats['p90']:.1f}%, "
        f"max {stats['max']:.1f}%; {stats['share_pinnable_slope']:.0%} at <=3%; "
        f"{stats['share_unholdable']:.1%} too steep to hold at stimp {stimp:g} (> {stats['hold_limit']:.1f}%)"
    )

    # Hole: the valid pin location closest to a back-left target.
    mask = valid_pin_mask(field_, boundary)
    emit(f"Valid pin area: {mask.sum() * field_.spacing**2:.0f} m^2")
    if not mask.any():
        raise NoValidPinError(
            f"No valid hole location on green #{seed} (nowhere is <=3% and 12 ft from the edge); try another seed"
        )
    X, Y = field_.meshgrid()
    d2 = np.where(mask, (X - 13.0) ** 2 + (Y - 20.0) ** 2, np.inf)
    j, i = np.unravel_index(np.argmin(d2), d2.shape)
    hole = Hole(float(X[j, i]), float(Y[j, i]))
    emit(f"Hole at ({hole.x:.2f}, {hole.y:.2f})")

    # Putts aimed straight at the hole at "30 cm past on flat" pace, so slopes show up as break.
    a = stimp_to_deceleration(stimp)
    putts = []
    t0 = time.perf_counter()
    for k in range(10):
        ang = math.radians(200 + k * 16)
        r = 5.0 + 1.5 * (k % 4)
        start = (hole.x + r * math.cos(ang), hole.y + r * math.sin(ang))
        if not boundary.contains(*start):
            continue
        speed = math.sqrt(2 * a * (r + 0.3))
        putts.append(roll_ball(field_, start, velocity_toward(start, (hole.x, hole.y), speed), stimp, hole, boundary))
    emit(f"{len(putts)} putts in {time.perf_counter() - t0:.2f}s, {sum(p.holed for p in putts)} holed (aimed straight, no break read)")

    cloud = None
    if scan != "none":
        t0 = time.perf_counter()
        if scan == "aerial":
            cloud = aerial_scan(field_, density=150, seed=seed)
        else:
            stations = [(4.0, 4.0), (32.0, 4.0), (18.0, 28.0)]
            cloud = PointCloud.concatenate(
                [terrestrial_scan(field_, s, seed=seed + n, source_id=n) for n, s in enumerate(stations)]
            )
        recon, coverage = points_to_heightfield(cloud.xyz, 0.1, field_.extent)
        on = boundary.mask(recon)
        rmse = np.sqrt(np.mean((recon.z - field_.height(*recon.meshgrid()))[on] ** 2))
        emit(
            f"{scan} scan: {len(cloud):,} points in {time.perf_counter() - t0:.1f}s; "
            f"on-green coverage {np.mean(coverage[on] > 0):.0%} of 10 cm cells; reconstruction RMSE {rmse * 1000:.1f} mm"
        )
    return Scene(field_, boundary, hole, putts, cloud, seed, stimp, summary)
