"""Ball-roll integration over a height field.

Model (pure rolling, skid phase ignored):

* Gravity: a rolling solid sphere on a surface tilted at angle theta is pulled
  downhill at (5/7)*g*sin(theta). Projected onto the horizontal plane, with
  gradient vector ``grad`` this is ``-(5/7)*g*grad / (1 + |grad|^2)``.
* Rolling resistance: constant deceleration ``a_roll`` (from the Stimpmeter
  reading), always opposing motion and never reversing it.
* The ball stops for good when its speed reaches zero and the slope pull is no
  greater than ``a_roll``. Otherwise it keeps creeping downhill.

Integration is semi-implicit Euler with a fixed step.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from greensim.constants import GRAVITY, ROLLING_SPHERE_FACTOR
from greensim.physics.hole import Hole
from greensim.physics.stimp import stimp_to_deceleration
from greensim.terrain.boundary import GreenBoundary
from greensim.terrain.heightfield import HeightField

OUTCOMES = ("stopped", "holed", "off_green", "off_grid", "timeout")


@dataclass
class PuttResult:
    path: np.ndarray  # (N, 2) x, y positions
    times: np.ndarray  # (N,)
    speeds: np.ndarray  # (N,)
    outcome: str

    @property
    def final_position(self) -> tuple[float, float]:
        return float(self.path[-1, 0]), float(self.path[-1, 1])

    @property
    def distance(self) -> float:
        """Path length (m) along the ground (horizontal projection)."""
        return float(np.sum(np.hypot(*np.diff(self.path, axis=0).T)))

    @property
    def duration(self) -> float:
        return float(self.times[-1])

    @property
    def holed(self) -> bool:
        return self.outcome == "holed"


def roll_ball(
    green: HeightField,
    start: tuple[float, float],
    velocity: tuple[float, float],
    stimp_ft: float,
    hole: Hole | None = None,
    boundary: GreenBoundary | None = None,
    dt: float = 1e-3,
    max_time: float = 60.0,
    record_every: int = 10,
) -> PuttResult:
    """Simulate one putt from ``start`` with initial horizontal ``velocity`` (m/s).

    If ``boundary`` is given, the ball stops with outcome "off_green" when it
    leaves the putting surface. The fringe is not modelled yet.
    """
    a_roll = stimp_to_deceleration(stimp_ft)
    k = ROLLING_SPHERE_FACTOR * GRAVITY

    on_green = boundary.mask(green) if boundary is not None else None
    x0, y0 = green.origin
    h = green.spacing
    xmin, xmax, ymin, ymax = green.extent

    x, y = float(start[0]), float(start[1])
    vx, vy = float(velocity[0]), float(velocity[1])
    t = 0.0
    step = 0
    path, times, speeds = [(x, y)], [0.0], [math.hypot(vx, vy)]
    outcome = "timeout"

    while t < max_time:
        gx, gy = green.gradient_at(x, y)
        g2 = gx * gx + gy * gy
        pull = k / (1.0 + g2)
        vx -= pull * gx * dt
        vy -= pull * gy * dt

        speed = math.hypot(vx, vy)
        new_speed = speed - a_roll * dt
        if new_speed <= 0.0:
            vx = vy = 0.0
            new_speed = 0.0
        else:
            scale = new_speed / speed
            vx *= scale
            vy *= scale

        x += vx * dt
        y += vy * dt
        t += dt
        step += 1

        if hole is not None and hole.captures(x, y, new_speed):
            outcome = "holed"
            break
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            outcome = "off_grid"
            break
        if on_green is not None and not on_green[int(round((y - y0) / h)), int(round((x - x0) / h))]:
            outcome = "off_green"
            break
        if new_speed == 0.0 and pull * math.sqrt(g2) <= a_roll:
            outcome = "stopped"
            break
        if step % record_every == 0:
            path.append((x, y))
            times.append(t)
            speeds.append(new_speed)

    if (path[-1][0], path[-1][1]) != (x, y):
        path.append((x, y))
        times.append(t)
        speeds.append(math.hypot(vx, vy))
    return PuttResult(np.array(path), np.array(times), np.array(speeds), outcome)


def velocity_toward(start: tuple[float, float], target: tuple[float, float], speed: float) -> tuple[float, float]:
    """Velocity vector of magnitude ``speed`` aimed from ``start`` at ``target``."""
    dx, dy = target[0] - start[0], target[1] - start[1]
    d = math.hypot(dx, dy)
    if d == 0:
        raise ValueError("start and target coincide")
    return speed * dx / d, speed * dy / d
