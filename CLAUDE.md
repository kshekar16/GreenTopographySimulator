# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python package `greensim` (src layout) that simulates golf putting greens: height-field
topography, ball-roll physics, pin-location rules, simulated LIDAR scans, and 3D viewing
with PyVista. Research notes backing the constants and models live in
`docs/golf-green-standards.md`.

## Environment & commands

Python 3.12 is installed per-user at `C:\Users\kavee\AppData\Local\Programs\Python\Python312`
(the bare `python` on PATH may resolve to the Microsoft Store stub). Use the project venv:

```sh
.venv/Scripts/python.exe -m pip install -e ".[web,dev]"   # install / refresh deps
.venv/Scripts/python.exe -m pytest                         # all tests
.venv/Scripts/python.exe -m pytest tests/test_physics.py -k brede   # single test
.venv/Scripts/greensim.exe render -o data/demo.png         # headless render
.venv/Scripts/greensim.exe serve                           # browser viewer on :8080
```

## Container

- `Containerfile` builds a headless image. Its entry point is `greensim` and the default command is `serve --host 0.0.0.0`. Rendering uses OSMesa via `VTK_DEFAULT_OPENGL_WINDOW=vtkOSOpenGLRenderWindow`.
- `.github/workflows/container.yml` runs pytest, builds the image, and smoke-tests `render`, `scan` and `serve` inside it. On pushes to main and `v*` tags it then publishes amd64+arm64 to `ghcr.io/kshekar16/greentopographysimulator`. Podman and Docker are not installed locally, so CI is where the image actually gets verified.
- On this machine, Windows Application Control blocks one VTK DLL (`vtkIOH5Rage`), so a bare `import vtk` fails. Import from `vtkmodules.*` or go through pyvista.

## Conventions

- Units are SI metres and seconds throughout. The one exception is green speed: it is passed as the Stimpmeter reading in **feet** (`stimp_ft`).
- Grid layout: `HeightField.z[j, i]` is at `x = origin[0] + i*spacing` and `y = origin[1] + j*spacing`. Rows run along y. For PyVista `StructuredGrid`, flatten point data with `order="F"`.
- Directions are azimuths in degrees counter-clockwise from +x. In `sample_green`, +y is the back of the green.
- `HeightField.z` is read-only after construction, because the gradient grids are derived from it once.
- `greensim.viz` is kept out of `greensim/__init__` so the core does not import VTK or matplotlib.
- `greensim.scene.build_scene(seed, stimp, scan)` builds the demo scene for every command. The viewers take a `rebuild(seed, stimp)` callable to regenerate in place: `serve` runs it in a worker thread and only draws on the main thread, so keep `build_scene` free of VTK.
- In `viz/web.py`, always pass `server=server` to `plotter_ui`. Otherwise it registers its buttons on trame's default server and their trigger names collide with ours.
- Physics model: pure rolling (the skid phase is ignored), with constant rolling deceleration from the stimp reading and a `(5/7)·g·sinθ` slope pull. `tests/test_physics.py` checks it against the Brede formula. Keep that test passing when changing the integrator.
- `constants.MAX_CAPTURE_SPEED` and the hole-capture curve are unverified placeholders (see research notes §6).
- Simulated scans and real scans should both go through `lidar.points_to_heightfield`.
