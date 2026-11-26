import math

import pytest

from greensim.constants import FT, GRAVITY, ROLLING_SPHERE_FACTOR, STIMP_LAUNCH_SPEED
from greensim.physics import Hole, brede_speed, deceleration_to_stimp, roll_ball, stimp_to_deceleration
from greensim.physics.ball import velocity_toward
from greensim.terrain.generators import build, tilt


def test_stimp_roundtrip():
    a = stimp_to_deceleration(10.0)
    assert a == pytest.approx(STIMP_LAUNCH_SPEED**2 / (2 * 10 * FT))
    assert deceleration_to_stimp(a) == pytest.approx(10.0)


@pytest.mark.parametrize("stimp", [8.0, 10.0, 12.0, 14.0])
def test_flat_stimp_roll_matches_reading(stimp):
    flat = build(10, 4, 0.1, [])
    result = roll_ball(flat, (0.5, 2.0), (STIMP_LAUNCH_SPEED, 0.0), stimp)
    assert result.outcome == "stopped"
    assert result.distance == pytest.approx(stimp * FT, rel=0.005)


@pytest.mark.parametrize("slope_pct", [1.0, 2.0, 4.0])
def test_brede_formula_recovers_stimp_on_slope(slope_pct):
    """Uphill/downhill stimp rolls on a uniform slope + Brede = flat-ground reading."""
    stimp = 10.0
    slope = build(40, 4, 0.1, [tilt(slope_pct, 0.0)])  # falls toward +x
    down = roll_ball(slope, (1.0, 2.0), (STIMP_LAUNCH_SPEED, 0.0), stimp)
    up = roll_ball(slope, (39.0, 2.0), (-STIMP_LAUNCH_SPEED, 0.0), stimp)
    assert down.outcome == up.outcome == "stopped"
    assert up.distance < stimp * FT < down.distance
    assert brede_speed(up.distance, down.distance) / FT == pytest.approx(stimp, rel=0.01)


def test_ball_rolls_off_slope_too_steep_to_hold():
    stimp = 12.0
    a_roll = stimp_to_deceleration(stimp)
    hold_limit = a_roll / (ROLLING_SPHERE_FACTOR * GRAVITY)  # sin(theta) the ball can rest on
    steep = build(30, 4, 0.1, [tilt(100 * hold_limit * 1.3, 0.0)])
    result = roll_ball(steep, (2.0, 2.0), (0.0, 0.0), stimp, max_time=30)
    assert result.outcome == "off_grid"
    gentle = build(30, 4, 0.1, [tilt(100 * hold_limit * 0.7, 0.0)])
    result = roll_ball(gentle, (2.0, 2.0), (0.0, 0.0), stimp)
    assert result.outcome == "stopped" and result.distance < 1e-6


def test_putt_holed_at_right_pace_and_lips_out_when_hard():
    flat = build(10, 4, 0.05, [])
    hole = Hole(7.0, 2.0)
    stimp = 10.0
    a = stimp_to_deceleration(stimp)
    d = 6.0
    gentle = math.sqrt(2 * a * (d + 0.3))  # would finish 30 cm past
    assert roll_ball(flat, (1.0, 2.0), velocity_toward((1, 2), (7, 2), gentle), stimp, hole=hole).holed
    hard = math.sqrt(2 * a * (d + 4.0))
    assert not roll_ball(flat, (1.0, 2.0), velocity_toward((1, 2), (7, 2), hard), stimp, hole=hole).holed


def test_putt_breaks_downhill():
    side = build(10, 10, 0.05, [tilt(2.0, 270.0)])  # falls toward -y
    result = roll_ball(side, (1.0, 5.0), (2.0, 0.0), 10.0)
    assert result.final_position[1] < 5.0 - 0.1
