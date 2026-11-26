"""Command-line entry point: ``greensim <command>``.

    greensim view                 # desktop 3D window (needs a display)
    greensim serve                # 3D viewer in the browser at http://localhost:8080
    greensim render -o green.png  # off-screen render to an image
    greensim scan -o scan.las     # simulated LIDAR point cloud (.las or .ply)

Every command builds the same scene from the shared options: the sample green, a
hole, a fan of putts and a simulated scan. Pass ``--seed random`` for a surprise
green; in ``view`` and ``serve`` you can also generate new greens while running.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from greensim.scene import SCAN_TYPES, MAX_SEED, NoValidPinError, Scene, build_scene, random_seed

__all__ = ["main", "make_parser", "build_scene", "Scene"]

LAYERS = ("surface", "points", "putts")


def _seed(text: str) -> int:
    if text == "random":
        return random_seed()
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected an integer or 'random', got {text!r}") from None
    if not 0 <= value <= MAX_SEED:
        raise argparse.ArgumentTypeError(f"seed must be between 0 and {MAX_SEED}")
    return value


def _rebuilder(args):
    """Scene factory the viewers call to make a new green, keeping the other options."""
    return lambda seed, stimp: build_scene(seed, stimp, args.scan)


# --- commands ------------------------------------------------------------


def _cmd_view(args) -> None:
    from greensim.viz.view3d import show

    s = build_scene(args.seed, args.stimp, args.scan)
    show(
        s.field, s.boundary, s.cloud, s.putts, s.hole,
        exaggeration=args.exaggeration, hide=args.hide, scene=s, rebuild=_rebuilder(args),
    )


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
    out = Path(args.output)
    writers = {".las": write_las, ".ply": write_ply}
    writer = writers.get(out.suffix.lower())
    if writer is None:
        sys.exit("output must end in .las or .ply (.laz needs a compression backend and is not supported)")
    s = build_scene(args.seed, args.stimp, args.scan)
    out.parent.mkdir(parents=True, exist_ok=True)
    writer(out, s.cloud)
    print(f"Wrote {out} ({len(s.cloud):,} points)")


def _cmd_serve(args) -> None:
    from greensim.viz.web import serve

    s = build_scene(args.seed, args.stimp, args.scan)
    serve(
        s, host=args.host, port=args.port, exaggeration=args.exaggeration, hide=args.hide,
        open_browser=args.open, rebuild=_rebuilder(args),
    )


def make_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--seed", type=_seed, default=0, help="green to generate: 0-99999 or 'random' (default 0)")
    common.add_argument("--stimp", type=float, default=10.0, help="green speed in feet (default 10)")
    common.add_argument("--scan", choices=SCAN_TYPES, default="terrestrial", help="simulated LIDAR scan type")

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
    try:
        args.func(args)
    except NoValidPinError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
