"""Browser-based 3D viewer (trame + PyVista).

The scene is rendered on the server, off-screen, and streamed to the browser.
This is what runs in the container: no display or GPU is needed on either side.

The toolbar can generate a new green (a given seed, or a random one) at a chosen
green speed. Generation runs in a worker thread so the page stays responsive;
only the drawing happens on the server's main thread.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Sequence

import pyvista as pv

from greensim.viz.view3d import _set_camera, draw_scene

if TYPE_CHECKING:
    from greensim.scene import Scene

LAYERS = ("surface", "points", "putts")
STIMP_RANGE = (4.0, 16.0)


def serve(
    scene: "Scene",
    host: str = "localhost",
    port: int = 8080,
    exaggeration: float = 5.0,
    hide: Sequence[str] = (),
    open_browser: bool = False,
    rebuild: "Callable[[int, float], Scene] | None" = None,
) -> None:
    from trame.app import asynchronous, get_server
    from trame.ui.vuetify3 import SinglePageLayout
    from trame.widgets import html
    from trame.widgets import vuetify3 as v3
    from trame_pyvista.ui import plotter_ui

    from greensim.scene import MAX_SEED, NoValidPinError, random_seed

    plotter = pv.Plotter(off_screen=True)
    plotter.set_background("#1e1e24", top="#3a4a5c")
    layers: dict[str, list] = {}

    server = get_server(name="greensim", client_type="vue3")
    state, ctrl = server.state, server.controller
    for n in LAYERS:
        state[f"show_{n}"] = n not in hide
    state.busy = False
    state.error = ""

    def draw(s: "Scene") -> None:
        plotter.clear()
        layers.clear()
        layers.update(draw_scene(plotter, s.field, s.boundary, s.cloud, s.putts, s.hole, exaggeration))
        for n in LAYERS:
            for actor in layers.get(n, []):
                actor.SetVisibility(bool(state[f"show_{n}"]))
        state.summary = s.summary
        state.seed = s.seed
        state.stimp = s.stimp

    draw(scene)
    _set_camera(plotter, 1.4)

    # All three keys always exist in state, so this never registers a catch-all watcher.
    @state.change(*[f"show_{n}" for n in LAYERS])
    def _toggle(**kwargs):
        for n in LAYERS:
            for actor in layers.get(n, []):
                actor.SetVisibility(bool(kwargs[f"show_{n}"]))
        ctrl.view_update()

    async def _regenerate(seed: int, stimp: float) -> None:
        try:
            new = await asyncio.get_running_loop().run_in_executor(None, rebuild, seed, stimp)
        except (NoValidPinError, ValueError) as exc:
            with state:
                state.error = str(exc)
                state.busy = False
            return
        with state:
            draw(new)  # every green has the same footprint, so the camera stays where the user put it
            state.busy = False
        ctrl.view_update()

    def _parse_inputs() -> tuple[int, float] | None:
        try:
            seed, stimp = int(state.seed), float(state.stimp)
        except (TypeError, ValueError):
            state.error = "Seed must be a whole number and stimp a number"
            return None
        if not 0 <= seed <= MAX_SEED or not STIMP_RANGE[0] <= stimp <= STIMP_RANGE[1]:
            state.error = f"Seed must be 0-{MAX_SEED} and stimp {STIMP_RANGE[0]:g}-{STIMP_RANGE[1]:g} ft"
            return None
        return seed, stimp

    def generate() -> None:
        if state.busy or rebuild is None:
            return
        parsed = _parse_inputs()
        if parsed:
            state.busy = True  # set before yielding, so a double click can't start two builds
            state.error = ""
            asynchronous.create_task(_regenerate(*parsed))

    def new_green() -> None:
        if state.busy or rebuild is None:
            return
        state.seed = random_seed()
        generate()

    ctrl.generate, ctrl.new_green = generate, new_green  # also lets tests drive the buttons

    with SinglePageLayout(server) as layout:
        layout.title.set_text("Green Topography Simulator")
        with layout.toolbar:
            v3.VSpacer()
            if rebuild is not None:
                v3.VTextField(
                    v_model=("seed",), label="Seed", type="number", density="compact", hide_details=True,
                    style="max-width: 110px", classes="mx-1", disabled=("busy",), keyup_enter=generate,
                    __events=[("keyup_enter", "keyup.enter")],
                )
                v3.VTextField(
                    v_model=("stimp",), label="Stimp (ft)", type="number", step="0.5", density="compact",
                    hide_details=True, style="max-width: 110px", classes="mx-1", disabled=("busy",),
                    keyup_enter=generate, __events=[("keyup_enter", "keyup.enter")],
                )
                v3.VBtn("Generate", click=generate, loading=("busy",), variant="tonal", classes="mx-1")
                v3.VBtn(
                    "New green", click=new_green, disabled=("busy",), prepend_icon="mdi-dice-5",
                    variant="tonal", classes="mx-1",
                )
                v3.VDivider(vertical=True, classes="mx-2")
            for n in LAYERS:
                if layers.get(n):
                    v3.VCheckbox(
                        v_model=(f"show_{n}",), label=n.capitalize(), density="compact", hide_details=True,
                        classes="mx-1",
                    )
            v3.VProgressLinear(indeterminate=True, absolute=True, location="bottom", active=("busy",))
        with layout.content:
            with v3.VContainer(fluid=True, classes="pa-0 fill-height d-flex flex-column align-stretch"):
                with html.Div(classes="px-3 py-1 text-caption", style="font-family: monospace; width: 100%"):
                    v3.VAlert(
                        "{{ error }}", v_if=("error",), type="warning", density="compact", classes="my-1",
                    )
                    html.Div("{{ line }}", v_for="line in summary", key="line")
                with html.Div(style="flex: 1 1 auto; width: 100%; position: relative"):
                    # Pass our server: by default plotter_ui registers its menu buttons on trame's
                    # default server, which never runs, so they'd collide with our triggers.
                    view = plotter_ui(plotter, server=server, collapse_menu=True)
                    ctrl.view_update = view.update

    server.start(host=host, port=port, open_browser=open_browser, timeout=0)
