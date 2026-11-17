"""The dashboard: `sdlc.py board`, its state, its three routes and the page (075).

The board reads every open change as `status` does, and a factory run's files with copies of
`factory.py`'s parsing, pinned here. It writes nothing, and serves only a change's own files.
"""

from __future__ import annotations

import importlib.util
import json
import re
import socket
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load("sdlc_board_under_test", ROOT / "scripts" / "sdlc.py")
factory = _load("factory_board_pins", ROOT / "plugins" / "factory" / "scripts" / "factory.py")
board = sdlc._load_board()

INTENT = """\
---
id: {id}
slug: {slug}
tier: {tier}
stage: {stage}
created: 2026-11-17
updated: 2026-11-17
idea:
depends_on: {depends}
---

# {id} — {title}

## Problem

Written.

## Open questions

- {question}
"""


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", check=True
    )
    return out.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _change(root: Path, name: str, tier: int, stage: str, title: str, depends: str = "") -> Path:
    ident, slug = name.split("-", 1)
    folder = root / ".sdlc" / "work" / name
    _write(folder / "intent.md", INTENT.format(
        id=ident, slug=slug, tier=tier, stage=stage, title=title, depends=depends,
        question="Which drafts count?",
    ))  # fmt: skip
    return folder


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo on `main` with four open changes and a shipped one: a Tier 1 and a Tier 2 built by
    hand, a factory run ready to ship, and a factory run with a reply that isn't a review."""
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "README.md", "a repo\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")

    one = _change(root, "001-reopen-drafts", 1, "plan", "Reopen drafts")
    _write(one / "notes.md", "# Notes\n\n- [ ] say why a draft closes\n")

    two = _change(root, "002-draft-history", 2, "design", "Draft history", "[1]")
    _write(two / "spec.md", "# 002 — spec\n\n<Numbered requirements.>\n<Design.>\n<Contracts.>\n")
    _write(two / "checks.md", "# Checks\n\n## lists drafts\n\n```sh\ntrue\n```\n")

    three = _change(root, "003-draft-export", 2, "test", "Draft export")
    _write(three / "runs" / "builder.sessions", "s-1\n")
    _write(three / "build" / "round-1.md", "Built.\n")
    _write(three / "build" / "round-2.md", "Reworked.\n")
    _write(three / "reviews" / "round-1" / "code.md",
           "VERDICT: CHANGES\n- CHANGE: src/a.py:1: a\n- CHANGE: src/a.py:2: b\n")  # fmt: skip
    _write(three / "reviews" / "round-1" / "test.md", "VERDICT: PASS\n")
    _write(three / "reviews" / "round-1" / "verified.md",
           "- KEPT: code: src/a.py:1: a\n- DROPPED: code: src/a.py:2: b — not so\n")  # fmt: skip
    _write(three / "reviews" / "round-2" / "code.md", "VERDICT: PASS\n")
    _write(three / "decision.md", "DECISION: READY\n\nIt does what the spec says.\n")
    _write(three / "decisions.md", "# Decisions\n\n"
           "- [x] D1 (code round 1, default): CSV or JSON → decided: CSV\n"
           "- [ ] D2 (builder round 2, default): keep the old flag\n")  # fmt: skip

    four = _change(root, "004-draft-purge", 1, "build", "Draft purge")
    _write(four / "runs" / "builder.sessions", "s-2\n")
    _write(four / "reviews" / "round-1" / "code.md", "Looks fine to me.\n")
    _write(four / "decisions.md", "- [ ] D1 (code round 1, blocking): purge after 30 or 90 days?\n")

    _change(root, "005-old-thing", 1, "shipped", "Old thing")
    return root


def _cards(root: Path) -> dict[str, dict]:
    return {c["change"]: c for c in board.state(root)["changes"]}


@pytest.mark.portable
def test_every_open_change_is_on_the_board_with_its_next_step(repo) -> None:
    cards = _cards(repo)
    assert list(cards) == ["001-reopen-drafts", "002-draft-history", "003-draft-export",
                           "004-draft-purge"], "a shipped change is not open"  # fmt: skip
    one, two = cards["001-reopen-drafts"], cards["002-draft-history"]
    assert (one["tier"], one["stage"], one["mode"], one["column"]) == (1, "plan", "manual", "plan")
    assert one["next"] == "plan mode, then build it"
    assert one["title"] == "001 — Reopen drafts" and one["open_questions"] == 1
    assert one["undone"] == ["say why a draft closes"] and one["issue"] is None
    assert one["files"] == ["intent.md", "notes.md"] and one["problems"] == []
    assert (two["column"], two["next"]) == ("design", "plan mode, then build it")
    assert two["depends_on"] == ["001"] and two["unfilled"] == ["spec.md"] and two["checks"] == 1
    assert "rounds" not in two, "a change built by hand has no factory fields"


@pytest.mark.portable
def test_a_factory_run_shows_its_rounds_decision_and_ledger(repo) -> None:
    three = _cards(repo)["003-draft-export"]
    assert (three["mode"], three["column"], three["decision"]) == ("factory", "ready", "READY")
    assert three["next"].startswith("/sdlc:ship")
    first, second = three["rounds"]
    assert first["reviews"] == {"code": {"verdict": "CHANGES", "changes": 2},
                                "test": {"verdict": "PASS", "changes": 0}}  # fmt: skip
    assert first["verified"] == {"kept": 1, "dropped": 1} and first["built"]
    assert second["reviews"] == {"code": {"verdict": "PASS", "changes": 0}}
    assert second["verified"] is None and three["built"] == [1, 2]
    assert three["pending"] == [] and [d["id"] for d in three["assumed"]] == ["D2"]
    assert three["cost"] is None, "no runs/costs.jsonl: no figure, never a guess"


@pytest.mark.portable
def test_a_blocking_decision_or_an_unreadable_reply_needs_the_person(repo) -> None:
    four = _cards(repo)["004-draft-purge"]
    assert four["column"] == "needs-you"
    assert [d["text"] for d in four["pending"]] == ["purge after 30 or 90 days?"]
    assert any("round-1/code.md" in p for p in four["problems"])
    assert four["next"] == "answer its decision in the factory's supervisor"


def _worktree(
    root: Path, name: str, tier: int, stage: str, commit=(), dirty=(), factory=False
) -> Path:
    """A change in a worktree of its own, as `new --worktree` makes one, its intent committed on
    its branch, then a commit holding `commit` and uncommitted `dirty` paths."""
    tree = root / ".claude" / "worktrees" / name
    _git(root, "worktree", "add", "-q", "-b", name, str(tree), "main")
    folder = _change(tree, name, tier, stage, name.split("-", 1)[1])
    if factory:
        _write(folder / "runs" / "builder.sessions", "s-9\n")
    _git(tree, "add", "-A")
    _git(tree, "commit", "-q", "-m", f"wip {name[:3]}")
    for rel in commit:
        _write(tree / rel, "changed\n")
    if commit:
        _git(tree, "add", "-A")
        _git(tree, "commit", "-q", "-m", "build")
    for rel in dirty:
        _write(tree / rel, "edited\n")
    return folder


@pytest.mark.portable
def test_a_change_built_by_hand_moves_on_as_its_branch_and_review_do(repo) -> None:
    """Nothing moves `stage:` on a change built by hand between `plan` and `shipped` (080), so the
    board reads how far it has got from what it touched and whether ship's review has run."""
    _worktree(repo, "006-draft-tags", 1, "plan", commit=["src/tags.py"])
    _worktree(repo, "007-draft-notes", 1, "plan", commit=[".sdlc/work/inbox.md", ".sdlc/last-id"])
    _worktree(repo, "008-draft-sort", 1, "plan", dirty=["src/sort.py"])
    folder = _worktree(repo, "009-draft-share", 1, "plan", commit=["src/share.py"])
    _write(folder / "findings.md", "# Findings\n")
    _worktree(repo, "010-draft-sync", 2, "plan", commit=["src/sync.py"])
    _worktree(repo, "011-draft-lock", 1, "build", commit=["src/lock.py"], factory=True)
    cards = _cards(repo)
    seen = {n: (c["column"], c["seen"]) for n, c in cards.items() if n >= "006"}
    assert seen == {
        "006-draft-tags": ("build", "build"),
        "007-draft-notes": ("plan", None),  # only its folder, the register and the counter
        "008-draft-sort": ("build", "build"),  # uncommitted, in its own worktree
        "009-draft-share": ("test", "test"),
        "010-draft-sync": ("plan", None),  # a Tier 2 with no spec yet
        "011-draft-lock": ("build", None),  # the factory moves its own stage line
    }
    assert cards["006-draft-tags"]["next"] == "build it, then /sdlc:ship"
    assert cards["009-draft-share"]["next"] == "/sdlc:ship"
    assert cards["001-reopen-drafts"]["column"] == "plan", "no branch: nothing to read"
    assert cards["006-draft-tags"]["stage"] == "plan", (
        "the board reads its stage line, never writes it"
    )


@pytest.mark.portable
def test_a_shipped_change_waits_on_close_until_its_worktree_goes(served) -> None:
    root, url, _ = served
    _worktree(root, "012-draft-pins", 1, "shipped", commit=["src/pins.py"])
    card = _cards(root)["012-draft-pins"]
    assert (card["column"], card["next"]) == ("close", "/sdlc:close 012")
    assert "005-old-thing" not in _cards(root), "shipped with no worktree: closed already"
    query = urllib.parse.urlencode({"change": "012-draft-pins", "path": "intent.md"})
    assert _get(f"{url}/file?{query}")[0] == 200
    _git(
        root,
        "worktree",
        "remove",
        "--force",
        str(root / ".claude" / "worktrees" / "012-draft-pins"),
    )
    assert "012-draft-pins" not in _cards(root)
    assert _get(f"{url}/file?{query}")[0] == 404


@pytest.mark.portable
def test_the_cost_is_summed_as_the_factory_sums_it(repo) -> None:
    folder = repo / ".sdlc" / "work" / "003-draft-export"

    def row(session, role, model, ms, usd=None) -> dict:
        out = {"session": session, "role": role, "model": model, "duration_ms": ms}
        return out if usd is None else {**out, "cost_usd": usd}

    rows = [
        row("s-1", "builder", "opus", 60000, 0.5),
        row("s-1", "builder", "opus", 30000, 0.75),
        row("s-2", "code", "haiku", 1000, 0.1),
        row("s-3", "test", "haiku", 500),
    ]
    _write(folder / "runs" / "costs.jsonl", "".join(json.dumps(r) + "\n" for r in rows) + "{bad\n")
    mine, theirs = board.cost(folder), factory.run_cost(folder)
    for key in ("usd", "by_role", "by_model", "runs", "unknown"):
        assert mine[key] == theirs[key], key
    assert mine["usd"] == 0.85 and mine["duration_ms"] == 91500


@pytest.mark.portable
def test_the_factory_parsing_is_a_pinned_copy() -> None:
    for name in ("VERDICT_RE", "DECISION_RE", "CHANGE_RE", "KEPT_RE", "DROPPED_RE", "LEDGER_RE"):
        assert getattr(board, name).pattern == getattr(factory, name).pattern, name
    assert board.VERIFIED == factory.VERIFIED and board.COSTS == factory.COSTS


@pytest.mark.portable
def test_a_change_s_issue_link_is_built_from_the_remote_only_when_github_numbers_it(
    repo, monkeypatch
) -> None:
    _git(repo, "remote", "add", "origin", "git@github.com:someone/drafts.git")
    cfg = sdlc.load_config(repo)[0]
    assert board._issue_base(repo, cfg) is None, "local numbering has no issue to link"
    monkeypatch.setattr(sdlc, "ids_mode", lambda home, cfg: "github")
    assert board._issue_base(repo, cfg) == "https://github.com/someone/drafts/issues/"
    assert (
        _cards(repo)["002-draft-history"]["issue"] == "https://github.com/someone/drafts/issues/2"
    )


def test_status_never_loads_the_board() -> None:
    """R1: only `board`'s dispatch loads `board.py`, so no other command pays for it."""
    source = (ROOT / "scripts" / "sdlc.py").read_text(encoding="utf-8")
    calls = re.findall(r"(?<!def )_load_board\(\)", source)
    assert len(calls) == 1 and "return _load_board().cmd_board(root, args.port)" in source
    assert "board" not in vars(sdlc), "nothing binds it at import, as retro is bound"


# ---------------------------------------------------------------- the server


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def served(repo):
    port = _free_port()
    server = board.serve(repo, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield repo, f"http://127.0.0.1:{port}", port
    server.shutdown()
    server.server_close()


def _get(url: str, method: str = "GET", headers: dict | None = None) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


@pytest.mark.portable
def test_the_board_answers_three_gets_and_nothing_else(served) -> None:
    root, url, _ = served
    code, body, headers = _get(url + "/")
    assert code == 200 and b"<title>Change board</title>" in body
    assert headers["Content-Type"].startswith("text/html")
    code, body, _ = _get(url + "/state.json")
    st = json.loads(body)
    assert code == 200 and st["board"] == "sdlc" and len(st["changes"]) == 4
    code, body, _ = _get(url + "/file?change=001-reopen-drafts&path=notes.md")
    assert code == 200 and b"say why a draft closes" in body
    for method in ("POST", "PUT", "DELETE", "PATCH"):
        assert _get(url + "/state.json", method)[0] == 405, method
    assert _get(url + "/anything")[0] == 404
    assert _get(url + "/state.json", headers={"Host": "evil.example:80"})[0] == 404, "rebinding"


@pytest.mark.portable
def test_file_never_leaves_an_open_change_s_folder(served) -> None:
    root, url, _ = served
    (root / "secret.txt").write_text("nope\n", encoding="utf-8")
    folder = root / ".sdlc" / "work" / "001-reopen-drafts"
    for change, path in [
        ("001-reopen-drafts", "../../../secret.txt"),
        ("001-reopen-drafts", str(root / "secret.txt")),
        ("001-reopen-drafts", "missing.md"),
        ("009-no-such-change", "intent.md"),
        ("005-old-thing", "intent.md"),
        ("001-reopen-drafts", ""),
    ]:
        query = urllib.parse.urlencode({"change": change, "path": path})
        assert _get(f"{url}/file?{query}")[0] == 404, (change, path)
    try:
        (folder / "link.txt").symlink_to(root / "secret.txt")
    except OSError:
        return  # no symlinks without privileges on Windows: the rest has been checked
    assert _get(f"{url}/file?change=001-reopen-drafts&path=link.txt")[0] == 404


@pytest.mark.portable
def test_the_board_writes_nothing(served) -> None:
    root, url, _ = served
    _git(root, "add", "-A")
    before = _git(root, "status", "--porcelain", "--ignored")
    for path in ("/", "/state.json", "/file?change=003-draft-export&path=decision.md"):
        _get(url + path)
    _get(url + "/state.json", "POST")
    assert _git(root, "status", "--porcelain", "--ignored") == before


@pytest.mark.portable
def test_a_second_board_reports_the_first_and_anything_else_is_refused(
    served, capsys, tmp_path
) -> None:
    root, url, port = served
    assert board.cmd_board(root, port) == 0
    assert json.loads(capsys.readouterr().out) == {"url": f"{url}/", "serving": "already"}
    other = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
    threading.Thread(target=other.serve_forever, daemon=True).start()
    try:
        taken = other.server_address[1]
        assert board.cmd_board(root, taken) == 1
        assert f"port {taken}" in json.loads(capsys.readouterr().out)["refusals"][0]
    finally:
        other.shutdown()
        other.server_close()


# ---------------------------------------------------------------- the page


@pytest.mark.portable
def test_the_page_is_self_contained_and_never_parses_data_as_html() -> None:
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert not re.search(r"""(src|href)\s*=\s*["']?(https?:)?//""", page), "nothing external"
    assert "<link" not in page and "@import" not in page
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
        assert sink not in page, sink
    assert "textContent" in page
    for column in ("plan", "design", "build", "test", "ready", "needs-you"):
        assert f'key: "{column}"' in page, column


@pytest.mark.portable
def test_no_column_key_is_a_class_the_page_styles_on_its_own() -> None:
    # A card carries its column's key as a class (`card close`), so a rule for that class
    # anywhere but on a `.col` or a `.card` restyles every card in the column.
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    keys = set(re.findall(r'\{ key: "([^"]+)"', page))
    assert {"ready", "close", "needs-you"} <= keys
    css = re.search(r"<style>(.*?)</style>", page, re.S).group(1)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    clashes = []
    for block in re.findall(r"([^{}]+)\{", css):
        for selector in block.split(","):
            if selector.strip().startswith("@"):
                continue
            for compound in re.split(r"[\s>+~]+", selector.strip()):
                classes = set(re.findall(r"\.([A-Za-z_][\w-]*)", compound))
                if classes & keys and not classes & {"col", "card"}:
                    clashes.append(selector.strip())
    assert not clashes, clashes
