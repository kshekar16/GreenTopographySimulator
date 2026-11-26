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
