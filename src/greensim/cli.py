"""Command-line entry point: ``greensim <command>``.

    greensim view                 # desktop 3D window (needs a display)
    greensim serve                # 3D viewer in the browser at http://localhost:8080
    greensim render -o green.png  # off-screen render to an image
    greensim scan -o scan.las     # simulated LIDAR point cloud (.las or .ply)

Every command builds the same scene from the shared options: the sample green, a
hole, a fan of putts and a simulated scan.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from greensim.analysis import slope_stats, valid_pin_mask
from greensim.lidar import PointCloud, aerial_scan, points_to_heightfield, terrestrial_scan
from greensim.physics import Hole, PuttResult, roll_ball, stimp_to_deceleration
from greensim.physics.ball import velocity_toward
from greensim.terrain import GreenBoundary, HeightField
from greensim.terrain.generators import sample_green

LAYERS = ("surface", "points", "putts")


@dataclass
class Scene:
    field: HeightField
    boundary: GreenBoundary
    hole: Hole
    putts: list[PuttResult] = field(default_factory=list)
    cloud: PointCloud | None = None


def build_scene(seed: int = 0, stimp: float = 10.0, scan: str = "terrestrial", verbose: bool = True) -> Scene:
    """Generate the sample green, place a hole, roll putts and (optionally) scan it."""
    log = print if verbose else (lambda *a, **k: None)

    field_, boundary = sample_green(seed=seed)
    stats = slope_stats(field_, boundary, stimp)
    log(
        f"Green: {boundary.area:.0f} m^2, slope mean {stats['mean']:.1f}%, p90 {stats['p90']:.1f}%, "
        f"max {stats['max']:.1f}%; {stats['share_pinnable_slope']:.0%} at <=3%; "
        f"{stats['share_unholdable']:.1%} too steep to hold at stimp {stimp:g} (> {stats['hold_limit']:.1f}%)"
    )

    # Hole: the valid pin location closest to a back-left target.
    mask = valid_pin_mask(field_, boundary)
    log(f"Valid pin area: {mask.sum() * field_.spacing**2:.0f} m^2")
    X, Y = field_.meshgrid()
    d2 = np.where(mask, (X - 13.0) ** 2 + (Y - 20.0) ** 2, np.inf)
    j, i = np.unravel_index(np.argmin(d2), d2.shape)
    hole = Hole(float(X[j, i]), float(Y[j, i]))
    log(f"Hole at ({hole.x:.2f}, {hole.y:.2f})")

    # Putts aimed straight at the hole at "30 cm past on flat" pace, so slopes show up as break.
    a = stimp_to_deceleration(stimp)
    putts = []
    t0 = time.perf_counter()
    for k in range(10):
        ang = math.radians(200 + k * 16)
        r = 5.0 + 1.5 * (k % 4)
        start = (hole.x + r * math.cos(ang), hole.y + r * math.sin(ang))
        if not boundary.contains(*start):
            continue
        speed = math.sqrt(2 * a * (r + 0.3))
        putts.append(roll_ball(field_, start, velocity_toward(start, (hole.x, hole.y), speed), stimp, hole, boundary))
    log(f"{len(putts)} putts in {time.perf_counter() - t0:.2f}s, {sum(p.holed for p in putts)} holed (aimed straight, no break read)")

    cloud = None
    if scan != "none":
        t0 = time.perf_counter()
        if scan == "aerial":
            cloud = aerial_scan(field_, density=150, seed=seed)
        else:
            stations = [(4.0, 4.0), (32.0, 4.0), (18.0, 28.0)]
            cloud = PointCloud.concatenate(
                [terrestrial_scan(field_, s, seed=seed + n, source_id=n) for n, s in enumerate(stations)]
            )
        recon, coverage = points_to_heightfield(cloud.xyz, 0.1, field_.extent)
        on = boundary.mask(recon)
        rmse = np.sqrt(np.mean((recon.z - field_.height(*recon.meshgrid()))[on] ** 2))
        log(
            f"{scan} scan: {len(cloud):,} points in {time.perf_counter() - t0:.1f}s; "
            f"on-green coverage {np.mean(coverage[on] > 0):.0%} of 10 cm cells; reconstruction RMSE {rmse * 1000:.1f} mm"
        )
    return Scene(field_, boundary, hole, putts, cloud)


# --- commands ------------------------------------------------------------


def _cmd_view(args) -> None:
    from greensim.viz.view3d import show

    s = build_scene(args.seed, args.stimp, args.scan)
    show(s.field, s.boundary, s.cloud, s.putts, s.hole, exaggeration=args.exaggeration, hide=args.hide)


def _cmd_render(args) -> None:
    from greensim.viz.view3d import show

    s = build_scene(args.seed, args.stimp, args.scan)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    show(
        s.field, s.boundary, s.cloud, s.putts, s.hole,
        exaggeration=args.exaggeration, hide=args.hide, screenshot=str(out), off_screen=True,
    )
    print(f"Wrote {out}")


def _cmd_scan(args) -> None:
    from greensim.lidar import write_las, write_ply

    if args.scan == "none":
        sys.exit("--scan none produces no points")
    s = build_scene(args.seed, args.stimp, args.scan)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".ply":
        write_ply(out, s.cloud)
    elif out.suffix.lower() in (".las", ".laz"):
        write_las(out, s.cloud)
    else:
        sys.exit("output must end in .las or .ply")
    print(f"Wrote {out} ({len(s.cloud):,} points)")


def _cmd_serve(args) -> None:
    from greensim.viz.web import serve

    s = build_scene(args.seed, args.stimp, args.scan)
    serve(s, host=args.host, port=args.port, exaggeration=args.exaggeration, hide=args.hide, open_browser=args.open)


def make_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--seed", type=int, default=0, help="random seed for the green (default 0)")
    common.add_argument("--stimp", type=float, default=10.0, help="green speed in feet (default 10)")
    common.add_argument("--scan", choices=["terrestrial", "aerial", "none"], default="terrestrial", help="simulated LIDAR scan type")

    view_opts = argparse.ArgumentParser(add_help=False)
    view_opts.add_argument("--exaggeration", type=float, default=5.0, help="vertical exaggeration (default 5)")
    view_opts.add_argument("--hide", nargs="*", default=[], choices=LAYERS, help="layers to start hidden")

    p = argparse.ArgumentParser(prog="greensim", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("view", parents=[common, view_opts], help="desktop 3D window")
    sp.set_defaults(func=_cmd_view)

    sp = sub.add_parser("serve", parents=[common, view_opts], help="3D viewer in the browser")
    sp.add_argument("--host", default="localhost", help="bind address (use 0.0.0.0 in a container)")
    sp.add_argument("--port", type=int, default=8080)
    sp.add_argument("--open", action="store_true", help="open the system browser")
    sp.set_defaults(func=_cmd_serve)

    sp = sub.add_parser("render", parents=[common, view_opts], help="render the 3D view to an image")
    sp.add_argument("-o", "--output", default="data/green.png")
    sp.set_defaults(func=_cmd_render)

    sp = sub.add_parser("scan", parents=[common], help="write the simulated LIDAR scan to .las/.ply")
    sp.add_argument("-o", "--output", default="data/scan.las")
    sp.set_defaults(func=_cmd_scan)
    return p


def main(argv: list[str] | None = None) -> None:
    args = make_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
