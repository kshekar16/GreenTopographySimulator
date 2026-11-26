"""Physical constants, Rules of Golf values and simulator defaults.

All lengths are SI metres unless the name says otherwise. Green speed is the one
exception: it is given in feet (the Stimpmeter convention). See
docs/golf-green-standards.md for sources.
"""

FT = 0.3048  # metres per foot
GRAVITY = 9.80665  # m/s^2

# --- Rules of Golf -------------------------------------------------------
HOLE_DIAMETER = 0.108  # 4.25 in
HOLE_MIN_DEPTH = 0.1016  # 4 in
BALL_DIAMETER = 0.04267  # min 1.68 in
BALL_MASS = 0.04593  # max 1.620 oz

# --- Stimpmeter ----------------------------------------------------------
STIMP_LAUNCH_SPEED = 1.83  # m/s (about 6 ft/s) at the foot of the ramp

# Rolling solid sphere: fraction of g*sin(theta) that accelerates the ball downhill.
ROLLING_SPHERE_FACTOR = 5.0 / 7.0

# Max speed at which a ball crossing the hole centre still drops in.
# PLACEHOLDER: not yet verified against Penner (2002) / Holmes (1991).
MAX_CAPTURE_SPEED = 1.31  # m/s

# --- Defaults / guidelines ----------------------------------------------
DEFAULT_STIMP_FT = 10.0
DEFAULT_GRID_SPACING = 0.05  # m
PIN_MAX_SLOPE_PCT = 3.0
PIN_LEVEL_RADIUS = 3 * FT  # ~0.91 m around the hole kept near level
PIN_MIN_EDGE_DISTANCE = 12 * FT  # ~4 paces from any edge
