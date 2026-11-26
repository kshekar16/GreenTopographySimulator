"""Drive the browser viewer's Generate / New green actions without a browser."""

import asyncio

import pytest

pytest.importorskip("trame")
pytest.importorskip("trame_pyvista")

from greensim.scene import build_scene  # noqa: E402


def _rebuild(seed, stimp):
    return build_scene(seed, stimp, "none", verbose=False)


async def _wait_idle(state, timeout=60.0):
    loop = asyncio.get_running_loop()
    end = loop.time() + timeout
    await asyncio.sleep(0.05)
    while state.busy:
        assert loop.time() < end, "regeneration did not finish"
        await asyncio.sleep(0.05)


def test_generate_and_new_green(monkeypatch):
    from trame.app import get_server
    from trame_server.core import Server

    import greensim.viz.web as web

    monkeypatch.setattr(Server, "start", lambda self, *a, **k: None)  # build the app, don't serve it

    async def run():
        web.serve(_rebuild(0, 10.0), rebuild=_rebuild)
        server = get_server(name="greensim")
        state, ctrl = server.state, server.controller
        assert state.seed == 0 and state.summary[0].startswith("Green #0:")

        # Generate with a chosen seed and speed.
        state.seed, state.stimp = 5, 12.0
        ctrl.generate()
        assert state.busy  # set immediately, so a second click is ignored
        await _wait_idle(state)
        assert state.error == ""
        assert state.summary[0].startswith("Green #5:") and "stimp 12" in state.summary[0]

        # New green picks a random seed.
        ctrl.new_green()
        await _wait_idle(state)
        assert state.summary[0].startswith(f"Green #{state.seed}:")

        # Bad input is reported, nothing is built.
        state.seed, state.stimp = "x", 10
        ctrl.generate()
        assert not state.busy and "whole number" in state.error

    asyncio.run(run())
