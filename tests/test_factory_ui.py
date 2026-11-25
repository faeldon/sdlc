"""The UI review: the `[ui]` table and its reviewers, the shots and the ports their server takes.

`factory.py` is loaded by path, once, in `factory_helpers.py`. Each test builds a scratch repo
on a change branch with its folder, as `/sdlc:intent` leaves one, so nothing here runs an agent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from factory_helpers import (
    FULL,
    LISTED,
    NAME,
    _build_report,
    _change,
    _git,
    _on_main,
    _review,
    _run,
    _touch,
    _verdicts,
    _verified,
    factory,
)

# ---------------------------------------------------------------- the [ui] table and its reviewers


UI = '[ui]\nserve = "serve {port}"\nshoot = "shoot {url} {out}"\npaths = ["web/"]\n'


def test_without_a_complete_ui_table_no_ui_review_runs(tmp_path, capsys) -> None:
    root = _change(tmp_path)
    _on_main(root, '[ui]\nserve = "serve {port}"\npaths = ["web/"]\n')
    _touch(root, "web/page.html")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    assert out["missing"] == [*FULL, "docs"], "no shoot command: no UI review"
    cfg = factory.load_config(root)[0]
    assert not factory.ui_complete(cfg["ui"]) and factory.max_runs(cfg) == 29


def test_the_ui_reviewers_join_on_a_ui_path_at_either_depth(tmp_path, capsys) -> None:
    root = _change(tmp_path, 1, config=LISTED)
    _on_main(root, UI)
    _touch(root, "src/a.py")
    _build_report(root, 1)
    out = _verdicts(root, capsys)
    light = ["code", "behaviour"]
    assert (out["depth"], out["missing"]) == ("light", [*light, "docs"]), "no UI path, no UI review"
    _touch(root, "web/page.html")
    out = _verdicts(root, capsys)
    every = [*light, "ui", "ux", "docs"]
    assert (out["depth"], out["missing"]) == ("light", every)
    for role in every:
        _review(root, 1, role, "VERDICT: CHANGES", f"web/page.html:1: {role} fix")
    _verified(root, 1, kept=[f"{r}: web/page.html:1: {r} fix" for r in every])
    (root / "web" / "page.html").unlink()
    _build_report(root, 2)
    out = _verdicts(root, capsys)
    assert out["depth"] == "light", "UI reviews never make a run full"
    assert out["missing"] == every, "a run that looked at the page keeps looking"
    # Each round: four reviewers, the two UI ones, the docs one, the arbiter, the rework and two
    # gate fixes.
    assert factory.max_runs(factory.load_config(root)[0]) == 2 + 3 * (4 + 2 + 1 + 2 + 2)


def test_ui_reviewers_are_never_chosen_and_the_table_is_the_base_branch_s(tmp_path) -> None:
    root = _change(tmp_path)
    _on_main(root, UI)
    (root / ".sdlc" / "factory.toml").write_text(
        'reviewers = ["code", "ui"]\n' + UI.replace("web/", "src/"), encoding="utf-8"
    )
    cfg, warnings = factory.load_config(root)
    assert cfg["ui"]["paths"] == ["web/"], "a change can't point the UI review elsewhere"
    assert cfg["reviewers"] == ["code"]
    assert any("'ui' joins on its own" in w for w in warnings)
    assert any("ui is read from the base branch" in w for w in warnings)
    table, wrong = factory._ui_table({"timeout": "soon", "widths": [[1, 2, 3]], "colour": 1})
    assert table["timeout"] == 60 and table["widths"] == factory.DEFAULTS["ui"]["widths"]
    assert len(wrong) == 3 and "unknown key ui.colour" in wrong


def test_ui_fixture_is_checked_like_the_other_keys() -> None:
    """R9: `fixture` is a path inside the checkout, unset by default; anything else is a warning
    that leaves it unset."""
    assert factory.DEFAULTS["ui"]["fixture"] is None
    table, wrong = factory._ui_table({"fixture": "tests/fixtures/board/changes"})
    assert (table["fixture"], wrong) == ("tests/fixtures/board/changes", [])
    for bad in (3, ["a"], "", "/etc/board", "tests/../../elsewhere", "..", "C:/board"):
        table, wrong = factory._ui_table({"fixture": bad})
        assert table["fixture"] is None and len(wrong) == 1, bad
        assert "ui.fixture" in wrong[0], bad
    assert "fixture" in factory._ui_table("nonsense")[1][0], "the table's message names it"


@pytest.mark.parametrize("role", ["ui", "ux"])
def test_the_ui_reviewers_scale_like_the_others(role) -> None:
    cfg = factory.load_config(Path("/nonexistent"))[0]
    assert factory.model_for(role, cfg, 1, "light") == "sonnet"
    assert factory.model_for(role, cfg, 2, "light") == "sonnet"
    assert factory.model_for(role, {**cfg, "models": {role: "opus"}}, 1, "light") == "opus"
    assert factory.model_for(role, {**cfg, "models": {role: "haiku"}}, 1, "light") == "haiku"


# ---------------------------------------------------------------- the shots


# A dev server and a screenshot command, as a host's `[ui]` would name them: the server writes its
# pid, then serves; the shooter writes a PNG to its `out` unless `FAKE_SHOOT_EXIT` says to fail.
FAKE_SERVE = """\
import http.server, os, sys
open(sys.argv[2], "w").write(str(os.getpid()))
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])),
                                http.server.SimpleHTTPRequestHandler).serve_forever()
"""
FAKE_SHOOT = """\
import os, sys
code = int(os.environ.get("FAKE_SHOOT_EXIT", "0"))
if not code:
    open(sys.argv[2], "wb").write(b"\\x89PNG fake " + sys.argv[1].encode())
print("shot " + sys.argv[1], file=sys.stderr)
sys.exit(code)
"""
SLEEPER = "import os, sys, time\nopen(sys.argv[1], 'w').write(str(os.getpid()))\ntime.sleep(60)\n"


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # A zombie still answers kill(0); `ps` says whether it has gone.
    state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
    return bool(state.stdout.strip()) and not state.stdout.strip().startswith("Z")


def _ui(tmp_path: Path, serve: str | None = None, **more) -> dict:
    py = sys.executable
    (tmp_path / "serve.py").write_text(FAKE_SERVE)
    (tmp_path / "shoot.py").write_text(FAKE_SHOOT)
    pid = tmp_path / "server.pid"
    table = {
        "serve": serve or f'"{py}" "{tmp_path / "serve.py"}" {{port}} "{pid}"',
        "shoot": f'"{py}" "{tmp_path / "shoot.py"}" "{{url}}" "{{out}}"',
        "paths": ["web/"], "pages": ["/", "/drafts/"], "timeout": 20, **more,
    }  # fmt: skip
    return factory._ui_table(table)[0]


def test_shots_start_the_declared_server_shoot_each_page_and_stop_it(tmp_path) -> None:
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    ui = _ui(tmp_path)
    paths, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert record["problem"] is None, record
    names = sorted(p.name for p in paths)
    assert names == ["drafts-1280x800.png", "drafts-390x844.png", "index-1280x800.png",
                     "index-390x844.png"]  # fmt: skip
    assert all(p.is_file() for p in paths)
    where = root / ".sdlc" / "reports" / "shots" / NAME / "round-1" / "ui"
    assert paths[0].parent == where and (where / "shots.json").is_file()
    assert (root / ".sdlc" / "reports" / ".gitignore").read_text() == "*\n"
    assert _git(root, "status", "--porcelain", "--", ".sdlc/reports") == "", "none reach git"
    assert not factory._answers("127.0.0.1", record["port"]), "the server it started is stopped"
    assert not _alive(int((tmp_path / "server.pid").read_text()))
    assert any("/drafts/" in s["command"] for s in record["shots"])
    first = record["shots"][0]["command"]
    assert first.endswith(f'"{(where / "index-1280x800.png").relative_to(root).as_posix()}"')
    # A round already shot is reused, never shot again.
    (tmp_path / "server.pid").unlink()
    again, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert again == paths and not (tmp_path / "server.pid").exists()


def test_shots_wait_for_the_server_where_the_url_says(tmp_path) -> None:
    """F1: the readiness check goes to `[ui] url`'s host, resolved to each of its addresses."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    ui = _ui(tmp_path, url="http://localhost:{port}", pages=["/"], widths=[[390, 844]])
    paths, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert record["problem"] is None and paths[0].is_file(), record
    assert "http://localhost:" in record["shots"][0]["command"]


def test_a_failed_shot_or_a_silent_server_still_stops_the_server(tmp_path, monkeypatch) -> None:
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_SHOOT_EXIT", "3")
    paths, record = factory.shots(root, folder, "round-1", _ui(tmp_path), "ui")
    assert "exited 3" in record["problem"] and not any(p.is_file() for p in paths)
    assert not _alive(int((tmp_path / "server.pid").read_text()))
    monkeypatch.delenv("FAKE_SHOOT_EXIT")
    (tmp_path / "sleep.py").write_text(SLEEPER)
    sleeper = f'"{sys.executable}" "{tmp_path / "sleep.py"}" "{tmp_path / "sleep.pid"}"'
    paths, record = factory.shots(root, folder, "round-2", _ui(tmp_path, sleeper, timeout=1), "ui")
    assert "didn't answer" in record["problem"]
    assert not _alive(int((tmp_path / "sleep.pid").read_text())), "never left running"


def test_a_ui_review_never_runs_blind(tmp_path, capsys, claude, monkeypatch) -> None:
    root = _change(tmp_path)
    ui = _ui(tmp_path)
    toml = "[ui]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in ui.items() if v is not None)
    _on_main(root, toml)
    _touch(root, "web/page.html")
    _build_report(root, 1)
    folder = root / ".sdlc" / "work" / NAME
    monkeypatch.setenv("FAKE_SHOOT_EXIT", "1")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "ui", None)
    assert code == 1 and "doesn't run blind" in out["refusals"][0] and not claude()
    assert not (folder / "reviews" / "round-1" / "ui.md").exists()
    monkeypatch.delenv("FAKE_SHOOT_EXIT")
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "ux", None)
    assert code == 0, out
    argv = claude()[-1]["argv"]
    assert argv[3] == "sdlc-factory:reviewer-ux" and "Screenshots: " in argv[1]
    assert "index-390x844.png" in argv[1] and "web/page.html" in argv[1]
    assert f"/shots/{NAME}/round-1/ux/index-390x844.png" in argv[1], "ux's own folder"
    assert (folder / "reviews" / "round-1" / "ux.md").is_file()
    assert (folder / "runs" / "reviewer-ux.sessions").is_file()


# A dev server that serves fixture data and writes into it, as a real one may: it refuses a copy an
# earlier server already wrote to, so only a fresh copy lets it answer.
FIXTURE_SERVE = """\
import http.server, os, sys
port, fixture, pid = sys.argv[1:4]
open(pid, "w").write(str(os.getpid()))
with open(os.path.join(fixture, "written.txt"), "x") as f:
    f.write(open(os.path.join(fixture, "seed.txt")).read())
http.server.ThreadingHTTPServer(("127.0.0.1", int(port)),
                                http.server.SimpleHTTPRequestHandler).serve_forever()
"""


def _fixture_ui(tmp_path: Path, root: Path, fixture: str = "fixtures/drafts") -> dict:
    (tmp_path / "fixture_serve.py").write_text(FIXTURE_SERVE)
    serve = f'"{sys.executable}" "{tmp_path / "fixture_serve.py"}" {{port}} {{fixture}} '
    serve += f'"{tmp_path / "server.pid"}"'
    return _ui(tmp_path, serve, fixture=fixture, pages=["/"], widths=[[390, 844]])


def test_shots_serve_a_fresh_copy_of_the_fixture(tmp_path) -> None:
    """R10: each shot serves its own copy of the fixture, the committed one never written, and the
    record names the copy by a path relative to the checkout."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    _touch(root, "fixtures/drafts/seed.txt")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a fixture")
    ui = _fixture_ui(tmp_path, root)
    paths, record = factory.shots(root, folder, "round-1", ui, "ui")
    assert record["problem"] is None, record
    copy = root / ".sdlc" / "reports" / "shots" / NAME / "round-1" / "ui" / "fixture"
    assert (copy / "written.txt").read_text() == "x\n", "the server read and wrote its copy"
    assert not (root / "fixtures" / "drafts" / "written.txt").exists()
    assert _git(root, "status", "--porcelain") == "", "the committed fixture is as it was"
    rel = copy.relative_to(root).as_posix()
    assert f" {rel} " in record["serve"]
    assert str(root) not in record["serve"], "the record names no machine's checkout"
    # A second label gets a clean copy of its own; a copy a failed attempt left is replaced.
    stale = root / ".sdlc" / "reports" / "shots" / NAME / "round-2" / "ui" / "fixture"
    stale.mkdir(parents=True)
    (stale / "written.txt").write_text("stale\n")
    _, record = factory.shots(root, folder, "round-2", ui, "ui")
    assert record["problem"] is None, record
    assert (stale / "written.txt").read_text() == "x\n"
    # A fixture that is one file is copied into the folder, and `{fixture}` names the file.
    _, record = factory.shots(
        root, folder, "round-3", _ui(tmp_path, "true", fixture="README.md"), "ui"
    )
    copied = (
        root / ".sdlc" / "reports" / "shots" / NAME / "round-3" / "ui" / "fixture" / "README.md"
    )
    assert copied.read_text() == "a repo\n"


def test_a_missing_fixture_refuses_the_ui_review(tmp_path, capsys, claude) -> None:
    """R11: a fixture the checkout lacks is a problem, so no server starts and the UI review is
    refused; a `serve` naming `{fixture}` with none set is a config warning."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    paths, record = factory.shots(root, folder, "round-1", _fixture_ui(tmp_path, root), "ui")
    assert "fixtures/drafts" in record["problem"] and "doesn't exist" in record["problem"]
    assert not (tmp_path / "server.pid").exists(), "no server started"
    ui = _fixture_ui(tmp_path, root)
    toml = "[ui]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in ui.items() if v is not None)
    _on_main(root, toml)
    _touch(root, "web/page.html")
    _build_report(root, 1)
    code, out = _run(capsys, factory.cmd_agent, root, "008", "review", "ui", None)
    assert code == 1 and "doesn't run blind" in out["refusals"][0] and not claude()
    _on_main(root, toml.replace('fixture = "fixtures/drafts"\n', ""))
    assert "ui.serve names {fixture}, but no ui.fixture is set" in factory.load_config(root)[1]


# A dev server that builds its data inside the fixture copy and refuses a copy that already holds
# it, as this repo's `serve.sh` does through `build.sh`.
BUILDING_SERVE = """\
import http.server, os, sys
port, fixture = sys.argv[1:3]
os.mkdir(os.path.join(fixture, "drafts"))
http.server.ThreadingHTTPServer(("127.0.0.1", int(port)),
                                http.server.SimpleHTTPRequestHandler).serve_forever()
"""


def test_the_ui_and_ux_reviews_of_a_round_run_at_once(
    tmp_path, capsys, claude, monkeypatch
) -> None:
    """119: the ui and ux reviewers started together each take their shots in a folder of their
    own, with their own fixture copy and server, so neither's serve finds the other's data."""
    import threading

    root = _change(tmp_path)
    _touch(root, "fixtures/drafts/seed.txt")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "a fixture")
    (tmp_path / "building_serve.py").write_text(BUILDING_SERVE)
    serve = f'"{sys.executable}" "{tmp_path / "building_serve.py"}" {{port}} {{fixture}}'
    ui = _ui(tmp_path, serve, fixture="fixtures/drafts", pages=["/"], widths=[[390, 844]])
    toml = "[ui]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in ui.items() if v is not None)
    _on_main(root, toml)
    _touch(root, "web/page.html")
    _build_report(root, 1)
    # Both copy their fixture before either serves, as two reviewers started together may.
    together, copy = threading.Barrier(2, timeout=20), factory._fixture_copy

    def held(*args):
        served = copy(*args)
        together.wait()
        return served

    monkeypatch.setattr(factory, "_fixture_copy", held)
    codes: dict = {}

    def review(role: str) -> None:
        codes[role] = factory.cmd_agent(root, "008", "review", role, None)

    threads = [threading.Thread(target=review, args=(role,)) for role in ("ui", "ux")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    printed = capsys.readouterr().out
    assert codes == {"ui": 0, "ux": 0}, printed
    folder = root / ".sdlc" / "work" / NAME
    shots = root / ".sdlc" / "reports" / "shots" / NAME / "round-1"
    for role in ("ui", "ux"):
        assert (folder / "reviews" / "round-1" / f"{role}.md").is_file()
        assert (shots / role / "fixture" / "drafts").is_dir()
        prompt = next(c["argv"][1] for c in claude() if c["argv"][3].endswith(f"-{role}"))
        assert f"Screenshots: {(shots / role / 'index-390x844.png').as_posix()}." in prompt


# ---------------------------------------------------------------- the shots' ports


def _held(listening: bool):
    """A socket holding a port on 127.0.0.1, as a parallel run's server would: one that answers,
    or one bound that a second server can't bind."""
    import socket

    held = socket.socket()
    held.bind(("127.0.0.1", 0))
    if listening:
        held.listen()
    return held


def test_shots_take_a_new_port_when_theirs_is_lost(tmp_path, monkeypatch) -> None:
    """111: a port another process takes between `_free_port()` and the serve is tried again on a
    new one, and the record says so: taken before the serve started (it already answers), or bound
    so the serve exits before answering. Every try lost is a problem, with no server left."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    ui = _ui(tmp_path, pages=["/"], widths=[[390, 844]])
    answering, bound = _held(True), _held(False)
    ports = [answering.getsockname()[1], bound.getsockname()[1]]
    free = iter([*ports, factory._free_port()])
    monkeypatch.setattr(factory, "_free_port", lambda: next(free))
    try:
        paths, record = factory.shots(root, folder, "round-1", ui, "ui")
        assert record["problem"] is None and paths[0].is_file(), record
        assert [r["port"] for r in record["retries"]] == ports, record
        assert "already answered" in record["retries"][0]["why"], record
        assert "exited" in record["retries"][1]["why"], record
        assert record["port"] not in ports and f" {record['port']} " in record["serve"]
        assert not _alive(int((tmp_path / "server.pid").read_text()))
        monkeypatch.setattr(factory, "_free_port", lambda: ports[0])
        (tmp_path / "server.pid").unlink()
        _, record = factory.shots(root, folder, "round-2", ui, "ui")
        assert len(record["retries"]) == factory.SERVE_TRIES, record
        assert "already answered" in record["problem"], record
        assert not (tmp_path / "server.pid").exists(), "no server started on a port taken"
    finally:
        answering.close()
        bound.close()


def test_a_port_is_lost_only_when_it_wont_bind_whichever_way_the_server_ended() -> None:
    """111 round 3: every way `_up()` sees the server end decides lost the same way, by whether the
    port binds. One that answered, then exited with the port free, failed on its own; one whose
    port is still held (another's server answering) lost it."""

    class Ended:
        """A server running on `held` when first asked, exited 1 when asked again, letting the
        port go when `frees`."""

        returncode = 1

        def __init__(self, held, frees: bool) -> None:
            self.held, self.frees, self.asked = held, frees, 0

        def poll(self) -> int | None:
            self.asked += 1
            if self.asked == 1:
                return None
            if self.frees:
                self.held.close()
            return 1

    for frees, lost in ((True, False), (False, True)):
        held = _held(True)
        port = held.getsockname()[1]
        try:
            why, got = factory._up(Ended(held, frees), "127.0.0.1", port, 5)
        finally:
            held.close()
        assert why == f"port {port} answered, but the dev server had exited 1", why
        assert got is lost, (frees, why)


def test_a_server_that_answered_and_closed_first_has_not_lost_its_port() -> None:
    """111 round 4: a server that answered a real request, closing the connection first as a
    server ending its reply does (its port's side left in TIME_WAIT), then exited on its own,
    failed on its own: its port is free to bind again, so it is not lost."""
    import socket

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
        conn, _ = listener.accept()
        conn.close()
        assert client.recv(1) == b"", "the server's side closed first"

    class Answered:
        """Running when first asked; exited 1, its port let go, when asked again."""

        returncode, asked = 1, 0

        def poll(self) -> int | None:
            self.asked += 1
            if self.asked == 1:
                return None
            listener.close()
            return 1

    try:
        why, lost = factory._up(Answered(), "127.0.0.1", port, 5)
    finally:
        listener.close()
    assert why == f"port {port} answered, but the dev server had exited 1", why
    assert lost is False, why


PROC_HEAD = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt\n"


@pytest.mark.portable
def test_only_time_wait_reads_the_proc_tables(tmp_path) -> None:
    """214: on Linux a TIME_WAIT left by a server that set no `SO_REUSEADDR` refuses a bind even
    from a socket that sets it, so a refused bind is held only while `/proc/net/tcp` or `tcp6`
    lists the port in a state other than TIME_WAIT (`06`); with no entry, the bind's word stands."""
    v4, v6 = tmp_path / "tcp", tmp_path / "tcp6"
    v4.write_text(
        PROC_HEAD
        + "   0: 0100007F:1F90 0100007F:D431 06 00000000:00000000 03:00000010 00000000\n"
        + "   1: 0100007F:D431 0100007F:1F90 06 00000000:00000000 03:00000010 00000000\n"
        + "   2: 00000000:0050 00000000:0000 0A 00000000:00000000 00:00000000 00000000\n",
        encoding="utf-8",
        newline="\n",
    )
    v6.write_text(
        PROC_HEAD
        + "   0: 00000000000000000000000001000000:0BB8 00000000000000000000000000000000:0000 0A"
        + " 00000000:00000000 00:00000000 00000000\n",
        encoding="utf-8",
        newline="\n",
    )
    tables = (v4, v6)
    assert factory._only_time_wait(0x1F90, tables) is True, "TIME_WAIT alone holds 8080"
    assert factory._only_time_wait(0x0050, tables) is False, "a listener holds 80"
    assert factory._only_time_wait(0x0BB8, tables) is False, "an IPv6 listener holds 3000"
    assert factory._only_time_wait(0x1234, tables) is False, "no entry: the bind's word"
    assert factory._only_time_wait(0x1F90, (tmp_path / "none",)) is False, "no table, not Linux"


@pytest.mark.skipif(os.name == "nt", reason="Windows binds a held port with SO_REUSEADDR")
def test_a_port_a_wildcard_listener_holds_is_lost() -> None:
    """111 ship F1: a server holding its port on every address (`0.0.0.0`) holds it for
    `127.0.0.1` too, so the port reads as held and a server that lost it is retried."""
    import socket

    with socket.socket() as held:
        held.bind(("0.0.0.0", 0))
        held.listen()
        port = held.getsockname()[1]
        assert factory._binds("127.0.0.1", port) is False
        assert factory._lost("127.0.0.1", port) is True


def test_a_server_that_fails_on_its_own_is_started_once(tmp_path, monkeypatch) -> None:
    """A serve that exits before answering, on a port that still binds, failed on its own, not
    because another process took the port: one start, no retry, and its exit is the problem."""
    root = _change(tmp_path)
    folder = root / ".sdlc" / "work" / NAME
    starts = tmp_path / "starts"
    serve = f'echo started >> "{starts}"; exit 1'
    ports = []
    real = factory._free_port
    monkeypatch.setattr(factory, "_free_port", lambda: ports.append(real()) or ports[-1])
    _, record = factory.shots(root, folder, "round-1", _ui(tmp_path, serve, timeout=5), "ui")
    assert starts.read_text().splitlines() == ["started"], "started once"
    assert len(ports) == 1 and record["retries"] == [], record
    assert "exited 1 before answering" in record["problem"], record


@pytest.mark.portable
def test_a_refused_bind_is_lost_only_when_more_than_a_time_wait_holds_it(monkeypatch) -> None:
    """235 R22: `_lost()` asks the table only when the bind is refused: a TIME_WAIT alone is not
    lost, a listener is, and a port that binds is never lost, whatever the table says."""
    for binds, time_wait, lost in [
        (False, True, False),
        (False, False, True),
        (True, True, False),
        (True, False, False),
    ]:
        monkeypatch.setattr(factory, "_binds", lambda host, port, binds=binds: binds)
        monkeypatch.setattr(factory, "_only_time_wait", lambda port, tw=time_wait: tw)
        assert factory._lost("127.0.0.1", 49152) is lost, (binds, time_wait)
