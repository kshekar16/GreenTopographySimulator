from greensim.cli import build_scene, main
from greensim.lidar import read_ply


def test_scan_command_writes_point_cloud(tmp_path):
    out = tmp_path / "scan.ply"
    main(["scan", "--scan", "aerial", "-o", str(out)])
    assert len(read_ply(out)) > 100_000


def test_build_scene_without_scan():
    scene = build_scene(scan="none", verbose=False)
    assert scene.cloud is None
    assert scene.putts and scene.boundary.contains(scene.hole.x, scene.hole.y)


def test_scan_rejects_unknown_suffix_before_building(tmp_path, monkeypatch):
    import pytest
    import greensim.cli as cli

    monkeypatch.setattr(cli, "build_scene", lambda *a, **k: pytest.fail("scene built before suffix check"))
    with pytest.raises(SystemExit):
        main(["scan", "-o", str(tmp_path / "scan.laz")])


def test_build_scene_fails_cleanly_without_valid_pin(monkeypatch):
    import numpy as np
    import pytest
    import greensim.cli as cli

    monkeypatch.setattr(cli, "valid_pin_mask", lambda f, b: np.zeros(f.z.shape, dtype=bool))
    with pytest.raises(SystemExit, match="No valid hole location"):
        build_scene(scan="none", verbose=False)
