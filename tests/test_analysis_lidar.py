import numpy as np
import pytest

from greensim.analysis import hold_limit_pct, slope_stats, valid_pin_mask
from greensim.lidar import aerial_scan, points_to_heightfield, read_las, read_ply, terrestrial_scan, write_las, write_ply
from greensim.terrain import GreenBoundary
from greensim.terrain.generators import build, sample_green, tier, tilt


def test_pin_mask_rejects_steep_and_edge_areas():
    field = build(30, 30, 0.1, [tilt(1.0, 270.0), tier(0.4, (15, 15), 90.0, 2.0)])  # bank ~20% at y=15
    boundary = GreenBoundary.ellipse(15, 15, 13, 13)
    mask = valid_pin_mask(field, boundary)
    X, Y = field.meshgrid()
    assert mask.any()
    assert not mask[np.abs(Y - 15) < 1.0].any()  # bank itself
    assert not mask[~boundary.mask(field)].any()  # off green
    assert not mask[boundary.edge_distance_grid(field) < 3.6].any()  # too close to edge


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_sample_green_meets_slope_guidelines(seed):
    field, boundary = sample_green(seed=seed)
    assert 400 < boundary.area < 650
    assert valid_pin_mask(field, boundary).sum() * field.spacing**2 > 80  # > 80 m^2 pinnable
    stats = slope_stats(field, boundary, stimp_ft=10.0)
    assert stats["share_unholdable"] == 0.0  # a ball can stop anywhere at stimp 10
    assert stats["share_pinnable_slope"] > 0.55  # most of the surface within the 3 % guideline


def test_hold_limit_matches_research_notes():
    # Research notes: sin(theta) < 0.078 at stimp 10, ~0.056 at 14; as grade (tan) that's 7.87 % / 5.61 %.
    assert hold_limit_pct(10.0) == pytest.approx(7.87, abs=0.02)
    assert hold_limit_pct(14.0) == pytest.approx(5.61, abs=0.02)


def test_aerial_scan_reconstructs_surface():
    field, _ = sample_green(seed=1, spacing=0.1)
    cloud = aerial_scan(field, density=200, noise_sigma=0.003, seed=0)
    recon, coverage = points_to_heightfield(cloud.xyz, 0.1, field.extent)
    assert recon.z.shape == field.z.shape
    err = recon.z - field.z
    assert np.sqrt(np.mean(err**2)) < 0.005


def test_terrestrial_scan_hits_surface_and_gets_sparser_with_range():
    field = build(40, 40, 0.1, [tilt(1.0, 0.0)])
    cloud = terrestrial_scan(field, (20.0, 20.0), range_noise_sigma=0.0, seed=0)
    assert len(cloud) > 1000
    np.testing.assert_allclose(cloud.xyz[:, 2], field.height(cloud.xyz[:, 0], cloud.xyz[:, 1]), atol=2e-3)
    r = np.hypot(cloud.xyz[:, 0] - 20, cloud.xyz[:, 1] - 20)
    near = (r < 5).sum() / (np.pi * 5**2)
    far = ((r > 12) & (r < 15)).sum() / (np.pi * (15**2 - 12**2))
    assert near > 5 * far


def test_terrestrial_scan_shadow_behind_crest():
    # Scanner low on the left; a 0.5 m ridge at x=20 hides the ground just behind it.
    field = build(40, 10, 0.05, [tier(0.5, (20, 5), 180.0, 0.5)])  # high side toward -x
    cloud = terrestrial_scan(field, (10.0, 5.0), instrument_height=0.3, seed=0)
    behind = (cloud.xyz[:, 0] > 20.5) & (cloud.xyz[:, 0] < 24) & (np.abs(cloud.xyz[:, 1] - 5) < 1)
    front = (cloud.xyz[:, 0] > 15) & (cloud.xyz[:, 0] < 18.5) & (np.abs(cloud.xyz[:, 1] - 5) < 1)
    assert front.sum() > 0 and behind.sum() == 0


@pytest.mark.parametrize("fmt", ["ply", "las"])
def test_point_cloud_io_roundtrip(tmp_path, fmt):
    field = build(5, 5, 0.1, [tilt(2.0, 45.0)])
    cloud = aerial_scan(field, density=50, seed=0)
    path = tmp_path / f"scan.{fmt}"
    (write_ply if fmt == "ply" else write_las)(path, cloud)
    back = (read_ply if fmt == "ply" else read_las)(path)
    assert len(back) == len(cloud)
    np.testing.assert_allclose(back.xyz, cloud.xyz, atol=1e-4)
    np.testing.assert_allclose(back.intensity, cloud.intensity, atol=1e-4)
