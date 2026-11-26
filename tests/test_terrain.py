import numpy as np
import pytest

from greensim.terrain import GreenBoundary, HeightField
from greensim.terrain.generators import build, tier, tilt


def test_plane_height_and_gradient_exact():
    # z = 0.02 x - 0.01 y + 1
    field = HeightField.from_function(lambda X, Y: 0.02 * X - 0.01 * Y + 1.0, 10, 8, 0.1)
    x, y = np.array([0.33, 5.07, 9.9]), np.array([0.12, 4.44, 7.95])
    np.testing.assert_allclose(field.height(x, y), 0.02 * x - 0.01 * y + 1.0, atol=1e-12)
    gx, gy = field.gradient(x, y)
    np.testing.assert_allclose(gx, 0.02, atol=1e-12)
    np.testing.assert_allclose(gy, -0.01, atol=1e-12)
    assert field.gradient_at(3.21, 6.54) == pytest.approx((0.02, -0.01), abs=1e-12)


def test_grid_geometry():
    field = HeightField.from_function(lambda X, Y: 0.0, 3.0, 2.0, 0.5, origin=(10, 20))
    assert field.z.shape == (5, 7)
    assert field.extent == (10, 13, 20, 22)


def test_tilt_slope_and_aspect():
    field = build(10, 10, 0.1, [tilt(2.0, 270.0)])  # falls toward -y
    np.testing.assert_allclose(field.slope_percent(), 2.0, atol=1e-9)
    np.testing.assert_allclose(field.aspect_degrees(), 270.0, atol=1e-6)


def test_tier_height_and_max_slope():
    field = build(20, 20, 0.05, [tier(0.3, (10, 10), 90.0, 3.0)])
    assert field.height(10, 19.9) - field.height(10, 0.1) == pytest.approx(0.3, abs=1e-3)
    assert field.slope_percent().max() == pytest.approx(100 * 0.3 / 3.0, rel=0.02)


def test_boundary_area_contains_and_edge_distance():
    b = GreenBoundary.ellipse(10, 10, 6, 4, n=720)
    assert b.area == pytest.approx(np.pi * 6 * 4, rel=1e-3)
    assert b.contains(10, 10) and not b.contains(16.5, 10)
    field = HeightField.from_function(lambda X, Y: 0.0, 20, 20, 0.05)
    dist = b.edge_distance_grid(field)
    j, i = int(round(10 / 0.05)), int(round(10 / 0.05))
    assert dist[j, i] == pytest.approx(4.0, abs=0.06)  # nearest edge is the minor axis
