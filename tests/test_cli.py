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
    import greensim.scene as scene_mod

    monkeypatch.setattr(scene_mod, "valid_pin_mask", lambda f, b: np.zeros(f.z.shape, dtype=bool))
    with pytest.raises(scene_mod.NoValidPinError, match="No valid hole location"):
        build_scene(scan="none", verbose=False)
    with pytest.raises(SystemExit, match="No valid hole location"):
        main(["render", "--scan", "none", "-o", "unused.png"])


def test_seed_option_accepts_random_and_rejects_junk(capsys):
    import pytest
    from greensim.cli import make_parser

    p = make_parser()
    assert 0 <= p.parse_args(["render", "--seed", "random"]).seed <= 99_999
    assert p.parse_args(["render", "--seed", "42"]).seed == 42
    for bad in ("abc", "-1", "100000"):
        with pytest.raises(SystemExit):
            p.parse_args(["render", "--seed", bad])


def test_scene_records_seed_and_summary():
    scene = build_scene(seed=7, stimp=11.5, scan="none", verbose=False)
    assert (scene.seed, scene.stimp) == (7, 11.5)
    assert scene.summary[0].startswith("Green #7:")
    assert any(line.startswith("Hole at") for line in scene.summary)
