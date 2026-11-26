"""Read and write point clouds: PLY (simple binary, for viewers) and LAS (the LIDAR standard)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from greensim.lidar.scanner import PointCloud

_PLY_DTYPE = np.dtype([("x", "<f8"), ("y", "<f8"), ("z", "<f8"), ("intensity", "<f4"), ("source_id", "<u2")])


def write_ply(path: str | Path, cloud: PointCloud) -> None:
    data = np.empty(len(cloud), dtype=_PLY_DTYPE)
    data["x"], data["y"], data["z"] = cloud.xyz.T
    data["intensity"] = cloud.intensity
    data["source_id"] = cloud.source_id
    header = (
        "ply\nformat binary_little_endian 1.0\n"
        f"element vertex {len(cloud)}\n"
        "property double x\nproperty double y\nproperty double z\n"
        "property float intensity\nproperty ushort source_id\nend_header\n"
    )
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        data.tofile(f)


def read_ply(path: str | Path) -> PointCloud:
    """Read a PLY written by :func:`write_ply` (not a general PLY reader)."""
    with open(path, "rb") as f:
        header = b""
        while not header.endswith(b"end_header\n"):
            line = f.readline()
            if not line:
                raise ValueError("invalid PLY: no end_header")
            header += line
        data = np.fromfile(f, dtype=_PLY_DTYPE)
    if b"property ushort source_id" not in header:
        raise ValueError("PLY was not written by greensim.write_ply")
    return PointCloud(np.column_stack([data["x"], data["y"], data["z"]]), data["intensity"], data["source_id"])


def write_las(path: str | Path, cloud: PointCloud, scale: float = 0.0001) -> None:
    """Write LAS 1.4 (point format 1). Coordinates are stored at ``scale`` m resolution."""
    import laspy

    header = laspy.LasHeader(point_format=1, version="1.4")
    header.scales = np.array([scale, scale, scale])
    header.offsets = cloud.xyz.min(axis=0) if len(cloud) else np.zeros(3)
    las = laspy.LasData(header)
    las.x, las.y, las.z = cloud.xyz.T
    las.intensity = np.round(np.clip(cloud.intensity, 0, 1) * 65535).astype(np.uint16)
    las.point_source_id = cloud.source_id
    las.classification = np.full(len(cloud), 2, dtype=np.uint8)  # 2 = ground
    las.write(str(path))


def read_las(path: str | Path) -> PointCloud:
    import laspy

    las = laspy.read(str(path))
    xyz = np.column_stack([np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)])
    intensity = np.asarray(las.intensity, dtype=float) / 65535.0
    return PointCloud(xyz, intensity, np.asarray(las.point_source_id, dtype=np.uint16))
