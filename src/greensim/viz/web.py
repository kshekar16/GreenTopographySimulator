"""Browser-based 3D viewer (trame + PyVista).

The scene is rendered on the server, off-screen, and streamed to the browser.
This is what runs in the container: no display or GPU is needed on either side.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import pyvista as pv

from greensim.viz.view3d import build_scene

if TYPE_CHECKING:
    from greensim.cli import Scene


def serve(
    scene: "Scene",
    host: str = "localhost",
    port: int = 8080,
    exaggeration: float = 5.0,
    hide: Sequence[str] = (),
    open_browser: bool = False,
) -> None:
    from trame.app import get_server
    from trame.ui.vuetify3 import SinglePageLayout
    from trame.widgets import vuetify3 as v3
    from trame_pyvista.ui import plotter_ui

    plotter = pv.Plotter(off_screen=True)
    plotter.set_background("#1e1e24", top="#3a4a5c")
    layers = build_scene(
        plotter, scene.field, scene.boundary, scene.cloud, scene.putts, scene.hole, exaggeration
    )
    plotter.camera_position = "iso"
    plotter.camera.elevation = -10
    plotter.reset_camera()
    plotter.camera.zoom(1.4)

    server = get_server(name="greensim", client_type="vue3")
    state, ctrl = server.state, server.controller
    names = [n for n in ("surface", "points", "putts") if layers.get(n)]
    for n in names:
        state[f"show_{n}"] = n not in hide
        for actor in layers[n]:
            actor.SetVisibility(n not in hide)

    @state.change(*[f"show_{n}" for n in names])
    def _toggle(**kwargs):
        for n in names:
            for actor in layers[n]:
                actor.SetVisibility(bool(kwargs[f"show_{n}"]))
        ctrl.view_update()

    with SinglePageLayout(server) as layout:
        layout.title.set_text("Green Topography Simulator")
        with layout.toolbar:
            v3.VSpacer()
            for n in names:
                v3.VCheckbox(v_model=(f"show_{n}",), label=n.capitalize(), density="compact", hide_details=True, classes="mx-2")
        with layout.content:
            with v3.VContainer(fluid=True, classes="pa-0 fill-height"):
                view = plotter_ui(plotter, collapse_menu=True)
                ctrl.view_update = view.update

    server.start(host=host, port=port, open_browser=open_browser, timeout=0)
