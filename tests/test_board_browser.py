"""The board's drawer, driven in a real browser: the keyboard behaviour `tests/test_board.py` can
only read in the page's source. Playwright is a `dev`-group dependency of this repo alone; no plugin
script declares or imports it. Without the library or its Chromium the test skips, saying which, so
`./check.sh` stays green on a machine that has neither (docs/CONTRIBUTING.md, *The gate*)."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "board"
INSTALL = "uv run --group dev playwright install --only-shell chromium"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_no_plugin_script_names_playwright() -> None:
    # A host runs these through `uv run --script`: Playwright there would reach every host.
    scripts = [*(ROOT / "scripts").rglob("*.py"), *(ROOT / "plugins").glob("*/scripts/**/*.py")]
    assert scripts
    named = [p for p in scripts if re.search("playwright", p.read_text("utf-8"), re.IGNORECASE)]
    assert named == []


@pytest.fixture
def board_url(tmp_path: Path):
    """The fixture board (`tests/fixtures/board/`) served on 127.0.0.1, on a port the OS picks,
    and shut down however the test ends."""
    root = tmp_path / "drafts"
    subprocess.run(
        ["sh", str(FIXTURE / "build.sh"), str(FIXTURE / "changes"), str(root)],
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    sdlc = _load("sdlc_board_browser", ROOT / "scripts" / "sdlc.py")
    server = sdlc._load_board().serve(root, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield root, f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def chromium():
    sync_api = pytest.importorskip(
        "playwright.sync_api", reason="playwright isn't installed: uv sync --group dev"
    )
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except sync_api.Error as e:
            # Headless runs its own build, so only a launch says whether the one it needs is here.
            if "Executable doesn't exist" not in str(e):
                raise
            pytest.skip(f"Chromium isn't installed: {INSTALL}")
        try:
            yield browser
        finally:
            browser.close()


IN_DRAWER = "() => document.getElementById('drawer').contains(document.activeElement)"
FOCUSABLE = """() => [...document.getElementById('drawer').querySelectorAll(
  'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')]
  .filter((n) => !n.closest('[hidden]')).length"""


@pytest.mark.browser
def test_the_drawer_holds_focus_and_returns_it_to_its_card(board_url, chromium) -> None:
    root, url = board_url
    page = chromium.new_page()
    page.goto(url)
    card = page.locator(".card").first
    card.wait_for()
    name = card.get_attribute("data-change")

    card.click()
    assert page.evaluate("() => document.activeElement.id") == "d-close"

    # Once round the drawer and past its last node: focus never leaves it.
    for _ in range(page.evaluate(FOCUSABLE) + 1):
        page.keyboard.press("Tab")
        assert page.evaluate(IN_DRAWER)
    page.keyboard.press("Shift+Tab")
    assert page.evaluate(IN_DRAWER)

    # A poll that finds the change moved rebuilds every card: the node the drawer opened from is
    # gone, and focus has to find the new one.
    old = card.element_handle()
    folder = next(root.glob(f".claude/worktrees/{name}/.sdlc/work/{name}"))
    (folder / "notes.md").write_text("# Notes\n", encoding="utf-8", newline="\n")
    page.wait_for_function("(el) => !el.isConnected", arg=old, timeout=10_000)

    page.keyboard.press("Escape")
    assert page.evaluate("() => document.getElementById('drawer').hidden")
    assert page.evaluate("() => document.activeElement.dataset.change") == name
