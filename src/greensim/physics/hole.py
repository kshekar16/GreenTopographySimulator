"""The hole and when a ball drops into it."""

from __future__ import annotations

import math
from dataclasses import dataclass

from greensim.constants import HOLE_DIAMETER, MAX_CAPTURE_SPEED


@dataclass
class Hole:
    x: float
    y: float
    diameter: float = HOLE_DIAMETER
    max_capture_speed_centre: float = MAX_CAPTURE_SPEED

    @property
    def radius(self) -> float:
        return self.diameter / 2.0

    def max_capture_speed(self, offset: float) -> float:
        """Fastest speed (m/s) at which a ball passing ``offset`` m from the centre still drops.

        PLACEHOLDER model: falls from the centre value to zero at the rim as
        sqrt(1 - (offset/r)^2). Replace this once the capture data is verified.
        """
        r = self.radius
        if offset >= r:
            return 0.0
        return self.max_capture_speed_centre * math.sqrt(1.0 - (offset / r) ** 2)

    def captures(self, x: float, y: float, speed: float) -> bool:
        offset = math.hypot(x - self.x, y - self.y)
        return offset < self.radius and speed <= self.max_capture_speed(offset)
