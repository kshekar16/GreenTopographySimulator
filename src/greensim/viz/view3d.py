"""Interactive 3D view (PyVista): surface, LIDAR points, putt paths and hole."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Sequence

import numpy as np
import pyvista as pv

from greensim.constants import BALL_DIAMETER
from greensim.lidar.scanner import PointCloud
from greensim.physics.ball import PuttResult
from greensim.physics.hole import Hole
from greensim.terrain.boundary import GreenBoundary
from greensim.terrain.heightfield import HeightField

if TYPE_CHECKING:
    from greensim.scene import Scene

_BAR_RIGHT = {"vertical": True, "position_x": 0.88, "position_y": 0.25, "height": 0.5, "width": 0.05}
_BAR_LEFT = {"vertical": True, "position_x": 0.05, "position_y": 0.25, "height": 0.5, "width": 0.05}

PUTT_COLORS = {"holed": "gold", "stopped": "white", "off_green": "orangered", "off_grid": "orangered", "timeout": "magenta"}


def _surface_mesh(field: HeightField, exaggeration: float) -> pv.StructuredGrid:
    X, Y = field.meshgrid()
    grid = pv.StructuredGrid(X, Y, field.z * exaggeration)
    grid["slope_pct"] = field.slope_percent().ravel(order="F")
    grid["elevation_m"] = field.z.ravel(order="F")
    return grid


def draw_scene(
    plotter: pv.Plotter,
    field: HeightField | None = None,
    boundary: GreenBoundary | None = None,
    cloud: PointCloud | None = None,
    putts: Sequence[PuttResult] = (),
    hole: Hole | None = None,
    exaggeration: float = 5.0,
    surface_scalars: str = "slope_pct",
    cloud_scalars: str = "elevation",
) -> dict[str, list]:
    """Add the given items to ``plotter``. Heights are scaled by ``exaggeration``.

    Returns the actors grouped by layer ("surface", "points", "putts") so callers can toggle them.
    """
    layers: dict[str, list] = {"surface": [], "points": [], "putts": []}
    if field is not None:
        mesh = _surface_mesh(field, exaggeration)
        clim = (0.0, 6.0) if surface_scalars == "slope_pct" else None
        bar = {"title": "Slope (%)" if surface_scalars == "slope_pct" else "Elevation (m)", **_BAR_RIGHT}
        if boundary is not None:
            mesh["on_green"] = boundary.mask(field).ravel(order="F").astype(float)
            green = mesh.threshold(0.5, scalars="on_green", preference="point")
            layers["surface"] += [
                plotter.add_mesh(mesh, color="#4a6b3a", opacity=0.6, show_scalar_bar=False),
                plotter.add_mesh(green, scalars=surface_scalars, cmap="viridis", clim=clim, scalar_bar_args=bar),
            ]
            edge = np.column_stack([boundary.vertices, field.height(*boundary.vertices.T) * exaggeration])
            plotter.add_mesh(pv.lines_from_points(np.vstack([edge, edge[:1]])), color="white", line_width=2)
        else:
            layers["surface"].append(
                plotter.add_mesh(mesh, scalars=surface_scalars, cmap="viridis", clim=clim, scalar_bar_args=bar)
            )

    if cloud is not None and len(cloud):
        pts = cloud.xyz * np.array([1.0, 1.0, exaggeration])
        poly = pv.PolyData(pts)
        if cloud_scalars == "intensity":
            poly["intensity"] = cloud.intensity
            actor = plotter.add_mesh(poly, scalars="intensity", cmap="gray", point_size=2, scalar_bar_args={"title": "Intensity", **_BAR_LEFT})
        else:
            poly["elevation_m"] = cloud.xyz[:, 2]
            actor = plotter.add_mesh(poly, scalars="elevation_m", cmap="terrain", point_size=2, scalar_bar_args={"title": "Points z (m)", **_BAR_LEFT})
        layers["points"].append(actor)

    if field is not None:
        lift = BALL_DIAMETER / 2
        for putt in putts:
            z = (field.height(*putt.path.T) + lift) * exaggeration
            line = pv.lines_from_points(np.column_stack([putt.path, z]))
            end = np.array([*putt.final_position, z[-1]])
            layers["putts"] += [
                plotter.add_mesh(line, color=PUTT_COLORS.get(putt.outcome, "white"), line_width=3),
                plotter.add_mesh(pv.Sphere(radius=lift * 1.5, center=end), color="white"),
            ]

        if hole is not None:
            hz = float(field.height(hole.x, hole.y)) * exaggeration + 0.002
            plotter.add_mesh(pv.Disc(center=(hole.x, hole.y, hz), inner=0.0, outer=hole.radius, c_res=48), color="black")
            plotter.add_mesh(pv.Line((hole.x, hole.y, hz), (hole.x, hole.y, hz + 2.1)), color="white", line_width=2)
            plotter.add_mesh(
                pv.Plane(center=(hole.x + 0.25, hole.y, hz + 1.9), direction=(0, 1, 0), i_size=0.5, j_size=0.35),
                color="red",
            )

    # Each colour bar belongs to its layer, so toggling the layer toggles its bar too.
    for title, bar_actor in plotter.scalar_bars.items():
        if title in ("Slope (%)", "Elevation (m)"):
            layers["surface"].append(bar_actor)
        elif title in ("Points z (m)", "Intensity"):
            layers["points"].append(bar_actor)

    plotter.add_text(f"vertical exaggeration x{exaggeration:g}", font_size=9, position="lower_right")
    plotter.show_axes()
    return layers


def _set_camera(plotter: pv.Plotter, zoom: float) -> None:
    plotter.camera_position = "iso"
    plotter.camera.elevation = -10
    plotter.reset_camera()
    plotter.camera.zoom(zoom)


def _add_layer_toggles(plotter: pv.Plotter, layers: dict[str, list], visible: dict[str, bool]) -> None:
    """Checkbox per non-empty layer, stacked in the top-left corner.

    The callbacks look the actors up in ``layers`` at click time, so the same
    checkboxes keep working after the scene is redrawn into that dict.
    """
    y = plotter.window_size[1] - 60
    for name in ("surface", "points", "putts"):
        if not layers.get(name):
            continue

        def toggle(state, name=name):
            visible[name] = bool(state)
            for a in layers.get(name, []):
                a.SetVisibility(state)

        plotter.add_checkbox_button_widget(toggle, value=visible[name], position=(10, y), size=30)
        plotter.add_text(name, position=(50, y + 4), font_size=10, name=f"label_{name}")
        y -= 40


def show(
    field: HeightField | None = None,
    boundary: GreenBoundary | None = None,
    cloud: PointCloud | None = None,
    putts: Sequence[PuttResult] = (),
    hole: Hole | None = None,
    exaggeration: float = 5.0,
    surface_scalars: str = "slope_pct",
    cloud_scalars: str = "elevation",
    screenshot: str | None = None,
    off_screen: bool = False,
    hide: Sequence[str] = (),
    scene: "Scene | None" = None,
    rebuild: "Callable[[int, float], Scene] | None" = None,
) -> None:
    """Open an interactive window. With ``off_screen=True``, only save ``screenshot``.

    ``hide`` lists layers ("surface", "points", "putts") that start hidden. In the
    window, checkboxes in the top-left toggle each layer.

    If ``rebuild(seed, stimp)`` is given, pressing ``n`` in the window replaces the
    scene with a new random green (``scene`` supplies the current stimp).
    """
    plotter = pv.Plotter(off_screen=off_screen, window_size=(1400, 900))
    plotter.set_background("#1e1e24", top="#3a4a5c")
    visible = {name: name not in hide for name in ("surface", "points", "putts")}
    layers: dict[str, list] = {}

    def draw(f, b, c, p, h, title: str | None) -> None:
        layers.clear()
        layers.update(draw_scene(plotter, f, b, c, p, h, exaggeration, surface_scalars, cloud_scalars))
        for name, actors in layers.items():
            for actor in actors:
                actor.SetVisibility(visible[name])
        if title:
            plotter.add_text(title, position="upper_edge", font_size=11, name="title")

    hint = "press n for a new green" if rebuild is not None and not off_screen else None
    title = f"Green #{scene.seed}" if scene is not None else None
    draw(field, boundary, cloud, putts, hole, " - ".join(t for t in (title, hint) if t))
    if not off_screen:
        _add_layer_toggles(plotter, layers, visible)

    if rebuild is not None and not off_screen:
        from greensim.scene import NoValidPinError, random_seed

        stimp = scene.stimp if scene is not None else 10.0

        def new_green() -> None:
            seed = random_seed()
            plotter.add_text(f"Generating green #{seed}...", position="upper_edge", font_size=11, name="title")
            plotter.render()
            try:
                s = rebuild(seed, stimp)
            except NoValidPinError as exc:
                plotter.add_text(f"{exc} - press n again", position="upper_edge", font_size=11, name="title")
                plotter.render()
                return
            camera = plotter.camera_position
            plotter.clear()  # actors, text and colour bars
            draw(s.field, s.boundary, s.cloud, s.putts, s.hole, f"Green #{s.seed} - {hint}")
            plotter.clear_button_widgets()  # re-add checkboxes with their labels, which clear() removed
            _add_layer_toggles(plotter, layers, visible)
            plotter.camera_position = camera
            plotter.render()

        plotter.add_key_event("n", new_green)

    _set_camera(plotter, 1.6)
    plotter.show(screenshot=screenshot, auto_close=True)
