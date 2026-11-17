"""The dashboard: `sdlc.py board`, its state, its three routes and the page (075).

The board reads every open change as `status` does, and a factory run's files with copies of
`factory.py`'s parsing, pinned here. It writes nothing, and serves only a change's own files.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
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
    assert "progress" not in one and "progress" not in two, "nor a step track"


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
    assert four["next"] == "fix what its problems name", "the problem first, as its column (098)"


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


def _main_check(root: Path, command: str) -> None:
    """`[commands] check` committed on `main`, the base branch, which the hand gate runs."""
    _write(root / ".sdlc" / "config.toml", f'[commands]\ncheck = "{command}"\n')
    _git(root, "add", ".sdlc/config.toml")
    _git(root, "commit", "-q", "-m", "gate")


def _hand_gate(tree: Path, ident: str) -> int:
    return sdlc.cmd_gate(tree, ident)


@pytest.mark.parametrize("stage", ["plan", "build"])
def test_a_green_gate_moves_a_hand_built_card_to_test_until_an_edit(repo, capsys, stage) -> None:
    """091 R8, R10: a current green record is `test`, `/sdlc:ship` next, before ship's review
    has run; an edit outside the change's folder makes it stale, and the card goes back."""
    _main_check(repo, "true")
    name = "012-draft-pins"
    folder = _worktree(repo, name, 1, stage, commit=["src/pins.py"])
    tree = sdlc.checkout_of(folder)
    card = _cards(repo)[name]
    assert (card["column"], card["gate"]) == ("build", None)
    assert _hand_gate(tree, "012") == 0
    capsys.readouterr()
    card = _cards(repo)[name]
    assert (card["column"], card["seen"], card["next"]) == ("test", "test", "/sdlc:ship")
    assert (card["gate"]["verdict"], card["gate"]["current"]) == ("PASS", True)
    assert card["stage"] == stage, "the board reads its stage line, never writes it"
    _write(tree / "src" / "pins.py", "edited again\n")
    card = _cards(repo)[name]
    assert (card["column"], card["gate"]["current"]) == ("build", False)
    assert card["next"] == "build it, then /sdlc:ship"


def test_a_red_gate_keeps_the_card_in_build_and_says_so(repo, capsys) -> None:
    """091 R9."""
    _main_check(repo, "exit 1")
    folder = _worktree(repo, "012-draft-pins", 1, "plan", commit=["src/pins.py"])
    assert _hand_gate(sdlc.checkout_of(folder), "012") == 1
    capsys.readouterr()
    card = _cards(repo)["012-draft-pins"]
    assert (card["column"], card["gate"]["verdict"], card["gate"]["current"]) == (
        "build", "FAIL", True,
    )  # fmt: skip
    assert card["next"] == "the gate is red: read build/gate.md, fix it, then sdlc.py gate 012"


@pytest.mark.portable
def test_a_factory_card_never_reads_a_hand_gate(repo) -> None:
    """091 R10: a factory run's gate is its own; a record in its folder moves nothing."""
    folder = _worktree(repo, "011-draft-lock", 1, "build", commit=["src/lock.py"], factory=True)
    _write(folder / "build" / "gate.md", "GATE: PASS\n\n## Attempt 1\n\nVerdict: PASS\n")
    card = _cards(repo)["011-draft-lock"]
    assert "gate" not in card and card["seen"] is None and card["column"] == "build"
    assert _cards(repo)["001-reopen-drafts"]["gate"] is None


@pytest.mark.portable
def test_the_gate_badge_is_built_as_text() -> None:
    """091 R10: the badge is a node of `h()`'s, only for a record that is current."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert '"gate green"' in page and '"gate red"' in page
    assert re.search(r"c\.gate && c\.gate\.current\s*\?\s*h\(", page)


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


# 078's round 1, as its run left it on 2026-11-17 (each long line cut at `…`): the reviewer asked
# for one change, and the verifier dropped it in other words than the reviewer's, so `verdicts`
# found the change answered no times and an answer to a change nobody asked for, and stopped.
STOP_CHANGE = (
    '.sdlc/REVIEW.md:50: The bullet says "The escapes from 047 and 050 are pinned by …" The commit'
    " history doesn't support that mapping. …"
)
STOP_DROPPED = (
    ".sdlc/REVIEW.md:50: the attribution of the two tests is wrong, so credit each to the change"
    " whose finding it pins."
)
STOP_PROBLEMS = [
    f"reviews/round-1/verified.md answers code: {STOP_CHANGE} 0 times, not once",
    f"reviews/round-1/verified.md answers code: {STOP_DROPPED}, which no review of round 1"
    " asks for",
]


def _stopped_run(root: Path, name: str = "013-draft-escapes", stage: str = "build") -> Path:
    """A factory run stopped as 078's was, after round 1's verification, with the record the
    supervisor's `verdicts --record` wrote from it:

        build/round-1.md            I added the two failure classes to `.sdlc/REVIEW.md`. …
                                    ## Evidence …
        reviews/round-1/code.md     VERDICT: CHANGES
                                    - CHANGE: .sdlc/REVIEW.md:50: The bullet says …
        reviews/round-1/verified.md - DROPPED: code: .sdlc/REVIEW.md:50: the attribution … — The
                                    attribution matches the history. …
    """
    folder = _change(root, name, 1, stage, "Review escape classes")
    _write(folder / "runs" / "builder.sessions", "s-3\n")
    _write(folder / "build" / "round-1.md", "I added the two failure classes to `.sdlc/REVIEW.md`."
           "\n\n## Evidence\n\n$ ./check.sh\n1848 passed\nexit: 0\n")  # fmt: skip
    _write(folder / "reviews" / "round-1" / "code.md",
           f"VERDICT: CHANGES\n\n- CHANGE: {STOP_CHANGE}\n\n## Notes\n\n- Fine.\n")  # fmt: skip
    _write(folder / "reviews" / "round-1" / "verified.md",
           f"- DROPPED: code: {STOP_DROPPED} — The attribution matches the history.\n")  # fmt: skip
    _write(folder / factory.STOPPED, factory.stop_text(name, "rerun", STOP_PROBLEMS))
    return folder


@pytest.mark.portable
def test_a_stopped_run_needs_the_person(repo) -> None:
    """R6: under Needs you, each problem as `verdicts` worded it, and the record's way on."""
    _stopped_run(repo)
    card = _cards(repo)["013-draft-escapes"]
    assert card["column"] == "needs-you"
    assert card["stopped"]["way"] == "rerun"
    assert card["stopped"]["problems"] == STOP_PROBLEMS
    assert card["next"] == factory.WAYS["rerun"].format(id="013")
    assert "the factory is building it" not in card["next"]
    assert card["problems"] == [], "a stop is not a file that won't read"


@pytest.mark.portable
def test_an_unreadable_stop_record_is_a_problem(repo) -> None:
    """R7: a record that won't read still puts the card in front of the person."""
    folder = _stopped_run(repo)
    _write(folder / factory.STOPPED, "stopped, somehow\n")
    card = _cards(repo)["013-draft-escapes"]
    assert card["column"] == "needs-you" and card["stopped"] is None
    assert any("runs/stopped.md" in p for p in card["problems"]), card["problems"]


@pytest.mark.portable
def test_a_stop_record_counts_only_at_build(repo) -> None:
    """R8: a run shipped by hand keeps its record in history, and the board reads past it."""
    _stopped_run(repo, "013-draft-escapes", "design")
    folder = _stopped_run(repo, "014-draft-stale", "test")
    _write(folder / "decision.md", "DECISION: READY\n")
    cards = _cards(repo)
    assert cards["013-draft-escapes"]["column"] == "design"
    assert cards["013-draft-escapes"]["stopped"] is None
    assert (cards["014-draft-stale"]["column"], cards["014-draft-stale"]["stopped"]) == (
        "ready",
        None,
    )
    shipped = _worktree(repo, "015-draft-shipped", 1, "shipped", commit=["src/x.py"], factory=True)
    _write(shipped / factory.STOPPED, "not even readable\n")
    card = _cards(repo)["015-draft-shipped"]
    assert (card["column"], card["problems"]) == ("close", [])


@pytest.mark.portable
def test_a_resumed_run_goes_back_to_build(repo) -> None:
    """R9: a reading that finds the cause gone removes the record, and the card is a run again."""
    folder = _stopped_run(repo)
    (folder / factory.STOPPED).unlink()
    card = _cards(repo)["013-draft-escapes"]
    assert (card["column"], card["stopped"]) == ("build", None)
    assert card["next"] == "the factory is building it: wait for its decision"


@pytest.mark.portable
def test_the_factory_parsing_is_a_pinned_copy() -> None:
    names = ("VERDICT_RE", "DECISION_RE", "CHANGE_RE", "KEPT_RE", "DROPPED_RE", "LEDGER_RE")
    for name in (*names, "STOPPED_RE", "NEXT_RE", "PROBLEM_RE"):
        assert getattr(board, name).pattern == getattr(factory, name).pattern, name
    assert board.VERIFIED == factory.VERIFIED and board.COSTS == factory.COSTS
    assert board.STOPPED == factory.STOPPED


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


@pytest.fixture
def served(repo):
    # Port 0 binds at once, so no other worker can take the port between choosing and binding it.
    server = board.serve(repo, 0)
    port = server.server_address[1]
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
    for host in ("127.0.0.1:0", "localhost:0", "127.0.0.1"):
        assert _get(url + "/state.json", headers={"Host": host})[0] == 404, host
    port = int(url.rsplit(":", 1)[1])
    assert _get(url + "/state.json", headers={"Host": f"localhost:{port}"})[0] == 200


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
    _closed(root, "019-draft-closed", 2)
    _run_at(root, "review", 1)
    _git(root, "add", "-A")
    before = _git(root, "status", "--porcelain", "--ignored")
    for path in ("/", "/state.json", "/file?change=003-draft-export&path=decision.md"):
        _get(url + path)
    assert json.loads(_get(url + "/state.json")[1])["changes"][-1]["progress"]["step"] == "review"
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


# ---------------------------------------------------------------- progress (088)

FULL = ["code", "security", "test", "behaviour"]


def _run_at(
    root: Path,
    step: str | None,
    rnd: int | None = 1,
    name: str = "016-draft-tags",
    tier: int = 2,
    since: str = "2026-11-17T10:00:00Z",
    after: str | None = None,
) -> Path:
    """A factory run at `stage: build` whose supervisor's last reading named `step`, the record
    written by `factory.py`'s own writer; `None` leaves no record."""
    folder = _change(root, name, tier, "build", "Draft tags")
    _write(folder / "runs" / "builder.sessions", "s-1\n")
    if step is not None:
        out = {"next": step, "round": rnd, "limit": 3, "reviewers": FULL}
        _write(folder / factory.STEP, factory.step_text(out, since, after))
    return folder


def _states(card: dict) -> list[str]:
    return [s["state"] for s in card["progress"]["steps"]]


TRACKS = {
    "build": ["current", "todo", "todo", "todo", "todo", "todo"],
    "gate": ["done", "current", "todo", "todo", "todo", "todo"],
    "fix": ["done", "current", "todo", "todo", "todo", "todo"],
    "review": ["done", "done", "current", "todo", "todo", "todo"],
    "verify": ["done", "done", "done", "current", "todo", "todo"],
    "rework": ["done", "done", "done", "done", "current", "todo"],
    "approve": ["done", "done", "done", "done", "done", "current"],
    "decide": ["done", "done", "paused", "todo", "todo", "todo"],
    "done": ["done"] * 6,
}


@pytest.mark.portable
@pytest.mark.parametrize("step", list(TRACKS))
def test_a_factory_card_shows_its_step_track(repo, step) -> None:
    """R4: the record's step is current, those before it done, those after it to do."""
    _run_at(repo, step, None if step in ("decide", "done") else 1, after="review")
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert [s["name"] for s in progress["steps"]] == list(board.TRACK)
    assert [s["state"] for s in progress["steps"]] == TRACKS[step]
    assert progress["step"] == step and progress["limit"] == 3
    labels = {s["name"]: s["label"] for s in progress["steps"]}
    assert (labels["gate"] == "fixing") == (step == "fix")
    if step in ("decide", "done"):
        assert progress["elapsed"] is None and progress["fraction"] is None, "no bar"
    else:
        assert progress["elapsed"] >= 0 and progress["round"] == 1


@pytest.mark.portable
def test_a_decision_or_a_stop_overrides_the_record(repo) -> None:
    """R4: a valid decision is every step done, at the stage it belongs to (098); a stop shown
    has no track at all."""
    folder = _run_at(repo, "review")
    _write(folder / "decision.md", "DECISION: ESCALATE\n\nAsk them.\n")
    intent = folder / "intent.md"
    intent.write_text(intent.read_text(encoding="utf-8").replace("stage: build", "stage: test"),
                      encoding="utf-8", newline="\n")  # fmt: skip
    assert _states(_cards(repo)["016-draft-tags"]) == ["done"] * 6
    stopped = _run_at(repo, "stop", None, name="017-draft-stop")
    _write(stopped / factory.STOPPED, factory.stop_text("017-draft-stop", "rerun", ["it broke"]))
    assert _cards(repo)["017-draft-stop"]["progress"] is None
    assert _cards(repo)["003-draft-export"]["progress"]["steps"][-1]["state"] == "done", "READY"


@pytest.mark.portable
def test_reviews_count_up_as_they_land(repo) -> None:
    """R5: `n` is counted on every request from the round's folder; `m` is the record's."""
    folder = _run_at(repo, "review", 2)
    review = _cards(repo)["016-draft-tags"]["progress"]["steps"][2]
    assert review["label"] == "reviews 0/4"
    _write(folder / "reviews" / "round-2" / "code.md", "VERDICT: PASS\n")
    _write(folder / "reviews" / "round-2" / "verified.md", "- KEPT: code: a\n")
    _write(folder / "reviews" / "round-1" / "test.md", "VERDICT: PASS\n")
    assert _cards(repo)["016-draft-tags"]["progress"]["steps"][2]["label"] == "reviews 1/4"
    _write(folder / "reviews" / "round-2" / "test.md", "VERDICT: CHANGES\n- CHANGE: a\n")
    assert _cards(repo)["016-draft-tags"]["progress"]["steps"][2]["label"] == "reviews 2/4"


@pytest.mark.portable
def test_a_first_build_runs_from_its_builder_session(repo) -> None:
    """R6: no record and no builder report: the build is current since `builder.sessions`."""
    folder = _run_at(repo, None)
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert _states({"progress": progress}) == TRACKS["build"] and progress["round"] == 1
    _write(folder / "build" / "round-1.md", "Built.\n")
    assert _cards(repo)["016-draft-tags"]["progress"] is None, "built, but no record: no track"


@pytest.mark.portable
def test_a_run_without_a_record_has_no_track(repo) -> None:
    """R6: a Tier 2 whose spec is still being drafted, or a run from before the record."""
    folder = _change(repo, "018-draft-spec", 2, "plan", "Draft spec")
    _write(folder / "runs" / "spec-writer.sessions", "s-1\n")
    cards = _cards(repo)
    assert cards["018-draft-spec"]["progress"] is None
    assert cards["001-reopen-drafts"].get("progress", "absent") == "absent", "by hand: no key"


@pytest.mark.portable
def test_a_garbled_step_record_is_a_problem(repo) -> None:
    folder = _run_at(repo, "review")
    _write(folder / factory.STEP, "running, probably\n")
    card = _cards(repo)["016-draft-tags"]
    assert card["progress"] is None
    assert any("runs/step.md" in p for p in card["problems"]), card["problems"]


@pytest.mark.portable
def test_the_step_record_is_a_pinned_copy(tmp_path) -> None:
    """R7: the board's copies are `factory.py`'s, and its writer reads back through the board."""
    for name in ("STEP_RE", "ROUND_RE", "LIMIT_RE", "REVIEWERS_RE", "SINCE_RE", "AFTER_RE",
                 "SECONDS_RE"):  # fmt: skip
        assert getattr(board, name).pattern == getattr(factory, name).pattern, name
    assert board.STEP == factory.STEP and board.REVIEWER_ROLES == factory.REVIEWERS
    gate = (ROOT / "plugins" / "factory" / "scripts" / "factory.py").read_text(encoding="utf-8")
    assert "Seconds: {seconds}" in gate and board.SECONDS_RE.match("Seconds: 12.5")
    for out in (
        {"next": "review", "round": 2, "limit": 3, "reviewers": [*FULL, "ui"]},
        {"next": "decide", "round": None, "limit": 2, "reviewers": ["code"]},
    ):
        text = factory.step_text(out, "2026-11-17T10:00:00Z", "rework")
        assert board.read_step(text) == factory.read_step(text)
        assert board.read_step(text)["reviewers"] == out["reviewers"]


def _row(role: str, seconds: float | None) -> tuple[str, dict]:
    return role, ({} if seconds is None else {"duration_ms": int(seconds * 1000)})


# One closed factory run, in the order its sessions ended: a build, two review rounds with a
# verification and a rework between them, the approver, then the landing's own review.
RUN = [
    _row("spec-writer", 300), _row("builder", 100), _row("code", 30), _row("test", 50),
    _row("verifier", 20), _row("builder", 40), _row("code", 10), _row("builder", None),
    _row("test", 12), _row("approver", 15), _row("code", 999), _row("builder", 999),
]  # fmt: skip


def _closed(root: Path, name: str, tier: int, rows=RUN, gates=(5.0, 6.0)) -> None:
    """A factory change closed on `main`: its folder committed with the rows `factory.py`'s own
    `record_cost()` writes and its gate file, then removed by a `Close` commit."""
    folder = _change(root, name, tier, "shipped", name.split("-", 1)[1])
    for i, (role, figures) in enumerate(rows):
        factory.record_cost(folder, f"s-{i}", role, "opus", figures)
    attempts = "".join(f"## Attempt {k}\n\nVerdict: PASS\nSeconds: {s}\n\n"
                       for k, s in enumerate(gates, 1))  # fmt: skip
    _write(folder / "build" / "round-1.gate.md", f"GATE: PASS\n\n{attempts}")
    _git(root, "add", "-A", str(folder))
    _git(root, "commit", "-q", "-m", f"Ship {name}")
    _git(root, "rm", "-rq", str(folder))
    _git(root, "commit", "-q", "-m", f"Close {name}")


@pytest.mark.portable
def test_typical_times_come_from_closed_factory_runs(repo) -> None:
    """R9: each step's samples, split by role and order, at the change's tier."""
    _closed(repo, "020-draft-a", 2)
    rows = [_row("builder", 200), _row("code", 70), _row("approver", 25)]
    _closed(repo, "021-draft-b", 2, rows, gates=(9.0,))
    _closed(repo, "022-draft-c", 2, rows, gates=())
    _closed(repo, "023-draft-d", 1, rows)
    _change(repo, "024-draft-manual", 2, "shipped", "Manual")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Close 024-draft-manual")
    samples = board.history_samples(repo, "main")
    assert samples[("build", 2)] == {"020-draft-a": [100], "021-draft-b": [200],
                                      "022-draft-c": [200]}  # fmt: skip
    assert samples[("review", 2)]["020-draft-a"] == [50, 12], "the slowest of each round"
    assert samples[("verify", 2)] == {"020-draft-a": [20]}
    assert samples[("rework", 2)] == {"020-draft-a": [40]}, "a row with no duration is skipped"
    assert samples[("approve", 2)]["020-draft-a"] == [15], "the landing's rows are not the run's"
    assert samples[("gate", 2)] == {"020-draft-a": [5.0, 6.0], "021-draft-b": [9.0]}
    assert set(samples[("build", 1)]) == {"023-draft-d"}
    table = board.typical_times(repo, "main")
    assert table["build/2"] == {"seconds": 200, "samples": 3}
    assert table["review/2"] == {"seconds": 60, "samples": 3}, "the median of every sample"
    assert "verify/2" not in table and "build/1" not in table, "fewer than 3 changes: no figure"


@pytest.mark.portable
def test_the_estimate_is_capped_and_absent_without_history(repo) -> None:
    """R8: the bar never passes 95%, and a tier with 2 sampled changes has no typical time."""
    rows = [_row("builder", 60), _row("code", 60), _row("approver", 60)]
    for name in ("030-draft-a", "031-draft-b"):
        _closed(repo, name, 2, rows)
    _run_at(repo, "build", since="2000-01-01T00:00:00Z")
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert progress["elapsed"] > 0
    assert (progress["typical"], progress["fraction"], progress["samples"]) == (None, None, None)
    _closed(repo, "032-draft-c", 2, rows)
    progress = _cards(repo)["016-draft-tags"]["progress"]
    assert (progress["typical"], progress["fraction"], progress["samples"]) == (60, 0.95, 3)
    fresh = board._progress(
        {"stage": "build", "tier": 2, "built": [1], "decision": None, "stopped": None},
        repo / ".sdlc" / "work" / "016-draft-tags",
        [],
        {"build/2": {"seconds": 600, "samples": 3}},
        board._since("2000-01-01T00:00:00Z") + 60,
    )
    assert (fresh["elapsed"], fresh["fraction"]) == (60, 0.1)


@pytest.mark.portable
def test_history_is_read_once_per_base_branch_tip(repo, monkeypatch) -> None:
    """R10: one `rev-parse` a request; the walk again only once the tip moves."""
    rows = [_row("builder", 60)]
    for name in ("040-draft-a", "041-draft-b", "042-draft-c"):
        _closed(repo, name, 2, rows)
    walks = []
    real = sdlc._git

    def counting(root, *args):
        if "log" in args and any("costs.jsonl" in a for a in args):
            walks.append(args)
        return real(root, *args)

    monkeypatch.setattr(sdlc, "_git", counting)
    board.state(repo)
    board.state(repo)
    assert len(walks) == 1, walks
    _closed(repo, "043-draft-d", 2, [_row("builder", 600)])
    board.state(repo)
    assert len(walks) == 2
    assert board.typical_times(repo, "main")["build/2"]["samples"] == 4


PLAN = """\
# 050 — plan

## Files to change

- `src/tags.py`: the tags.
- `docs/tags.md` (new): what they are.
- src/other.py: untouched yet, its width read from
  `progress.fraction` on a wrapped line, which names nothing.
- tests/: a test each.
- `<Path + one line on what happens to it.>`
- The docs, as their own lines.

## Work order

- `src/not-a-file-to-change.py`
"""


@pytest.mark.portable
def test_the_plan_hint_counts_named_files_the_branch_touched(repo) -> None:
    """R11: the named paths of `## Files to change` the branch or its worktree has touched."""
    commit = ["src/tags.py", "tests/test_tags.py"]
    folder = _worktree(
        repo, "050-draft-tags", 2, "build", factory=True, commit=commit, dirty=["docs/tags.md"]
    )
    _write(folder / "plan.md", PLAN)
    assert board._plan_named(PLAN) == ["src/tags.py", "docs/tags.md", "src/other.py", "tests/"]
    assert _cards(repo)["050-draft-tags"]["progress"]["plan"] == {"named": 4, "touched": 3}
    _write(folder / "plan.md", "# plan\n\n## Files to change\n\n<Path.>\n<More.>\n")
    assert _cards(repo)["050-draft-tags"]["progress"]["plan"] is None, "an unfilled plan"
    one = _worktree(repo, "051-draft-pins", 1, "build", factory=True, commit=["src/tags.py"])
    _write(one / "plan.md", PLAN)
    assert _cards(repo)["051-draft-pins"]["progress"]["plan"] is None, "a Tier 1 change"
    _write(folder / "plan.md", "# plan\n\n## Files to change\n\nThe usual ones.\n")
    assert _cards(repo)["050-draft-tags"]["progress"]["plan"] is None, "no path named"


@pytest.mark.portable
def test_the_bar_is_drawn_from_the_capped_fraction() -> None:
    """R13: the only width the page sets from data is `progress.fraction`'s, labelled an estimate,
    and the track's chips use no column key as a class."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    widths = re.findall(r"width:\s*\$\{([^}]*)\}", script)
    assert widths and all(re.fullmatch(r"Math\.round\(p\.fraction \* 100\)", w) for w in widths)
    assert "style" not in re.sub(r'style: `width: \$\{Math\.round\(p\.fraction \* 100\)\}%`', "",
                                 script), "no other style is set"  # fmt: skip
    assert "estimate" in script and "typical" in script and "files touched" in script
    assert "function progressRow(" in script and "progressRow(c.progress)" in script


@pytest.mark.portable
def test_a_step_s_state_is_in_its_text_and_the_bar_is_hidden_from_assistive_tech() -> None:
    """Round 1's ux changes: a step's state is said in its text, not by colour alone, and the bar,
    inside the card's button where a role would be dropped, is hidden; its figures are text."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    words = re.search(r"const STEP_WORDS = \{(.*?)\};", script, re.S)
    assert words, "each state has its own words"
    for state in ("done", "current", "paused"):
        assert re.search(rf'\b{state}: "[^"]+"', words.group(1)), state
    assert "progressbar" not in script
    assert re.search(r'class: "bar", "aria-hidden": "true"', script)


def _page_parts() -> tuple[str, str]:
    """The served page's stylesheet, comments dropped, and its script."""
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", page, re.S).group(1)
    script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S), script


@pytest.mark.portable
def test_needs_you_comes_first_at_phone_width_and_nowhere_else() -> None:
    """099 (2026-11-17-24): below 760px the columns stack, and the one waiting on the person
    leads them in the DOM, so Tab and a screen reader meet it first, as the eye does; the desktop
    grid keeps stage order, and no CSS `order` sets a look the DOM doesn't follow."""
    css, script = _page_parts()
    assert re.search(r"@media \(max-width: 760px\) \{\s*main\.board \{[^}]*1fr", css)
    assert 'window.matchMedia("(max-width: 760px)")' in script, "the same width as the CSS"
    order = re.search(r"function columnOrder\(\) \{(.*?)\n\}", script, re.S)
    assert order, "one place says the order"
    body = order.group(1)
    assert re.search(r"NARROW\.matches\s*\?\s*\[", body), "reordered only when narrow"
    assert re.search(r":\s*COLUMNS;", body), "stage order otherwise"
    assert body.index('=== "needs-you"') < body.index('!== "needs-you"'), "Needs you first"
    assert "columnOrder().map(" in script and "COLUMNS.map(" not in script
    assert re.search(r"JSON\.stringify\(\[NARROW\.matches, st\.changes\]\)", script), (
        "a width change is a change to render"
    )
    assert re.search(r'NARROW\.addEventListener\("change", [^\n]*render\(', script)
    assert not re.search(r"(?<![\w-])order:", css), "the DOM is the order"


@pytest.mark.portable
def test_the_open_drawer_keeps_tab_inside_it() -> None:
    """099 (2026-11-17-25): the drawer is aria-modal, so Tab and Shift-Tab cycle its focusable
    nodes, focus outside it is pulled back in, and Escape still closes it and returns focus."""
    _, script = _page_parts()
    trap = re.search(r"function trapTab\(e\) \{(.*?)\n\}", script, re.S)
    assert trap, "the trap's handler"
    body = trap.group(1)
    assert "querySelectorAll(FOCUSABLE)" in body and "e.preventDefault()" in body
    assert "e.shiftKey" in body and ".contains(document.activeElement)" in body
    handler = r'document\.addEventListener\("keydown", \(e\) => \{(.*?)\n\}\);'
    keys = re.search(handler, script, re.S)
    assert keys and "if (!open) return;" in keys.group(1)
    assert 'e.key === "Escape"' in keys.group(1) and 'e.key === "Tab"' in keys.group(1)
    assert "trapTab(e)" in keys.group(1)
    assert "back.focus()" in script, "focus returns to the card that opened it"
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert re.search(r'<div class="doc" tabindex="0"[^>]*aria-label="[^"]+"', page), (
        "the scrolling pane is a stop of the trap's, not a way out"
    )


@pytest.mark.portable
def test_the_verifier_chip_says_whose_count_it_is_in_its_text() -> None:
    """099 (2026-11-17-26): the count names the verifier in the text every user gets, not only in
    a tooltip."""
    _, script = _page_parts()
    chip = re.search(r"if \(r\.verified\) \{(.*?)\n  \}", script, re.S)
    assert chip
    assert re.search(r"`verifier: kept \$\{r\.verified\.kept\} · dropped", chip.group(1))


def _escalated(root: Path, name: str, stage: str, commit=()) -> Path:
    """A factory change in a worktree of its own, as a run leaves one the approver escalated: a
    round built and reviewed, `decision.md` saying ESCALATE, and `stage:` at whatever the person's
    answer moved it to."""
    folder = _worktree(root, name, 2, stage, commit=commit, factory=True)
    _write(folder / "build" / "round-1.md", "Built.\n\n## Evidence\n\n$ ./check.sh\nexit: 0\n")
    _write(folder / "reviews" / "round-1" / "code.md", "VERDICT: PASS\n")
    _write(folder / "decision.md", "DECISION: ESCALATE\n\nThe spec leaves the retention open.\n")
    return folder


@pytest.mark.portable
def test_each_factory_signal_counts_only_at_its_stage(repo) -> None:
    """086: the stage is the only mark of the person's answer, so an escalation, a stop or a
    pending decision the person has moved past leaves Needs you for the column that answer leads
    to."""
    _escalated(repo, "020-esc-shipped", "shipped", commit=["src/a.py"])
    _escalated(repo, "021-esc-dropped", "dropped")
    _escalated(repo, "022-esc-by-hand", "test", commit=["src/b.py"])
    _escalated(repo, "023-esc-back", "build")
    stopped = _worktree(repo, "024-stop-shipped", 1, "shipped", commit=["src/c.py"], factory=True)
    _write(stopped / factory.STOPPED, factory.stop_text("024", "rerun", STOP_PROBLEMS))
    pending = _worktree(repo, "025-pend-shipped", 1, "shipped", commit=["src/d.py"], factory=True)
    _write(pending / "decisions.md", "- [ ] D1 (code round 1, blocking): purge after 30 days?\n")
    at_test = _worktree(repo, "027-pend-test", 1, "test", commit=["src/f.py"], factory=True)
    _write(at_test / "decisions.md", "- [ ] D1 (code round 1, blocking): purge after 30 days?\n")
    cards = _cards(repo)
    got = {n: (c["column"], c["next"]) for n, c in cards.items() if n >= "020"}
    assert got == {
        "020-esc-shipped": ("close", "/sdlc:close 020"),
        "021-esc-dropped": ("close", "/sdlc:close 021"),
        "022-esc-by-hand": ("needs-you", "/sdlc:ship, or /sdlc-factory:land with the others ready"),
        "023-esc-back": ("build", "the factory is building it: wait for its decision"),
        "024-stop-shipped": ("close", "/sdlc:close 024"),
        "025-pend-shipped": ("close", "/sdlc:close 025"),
        "027-pend-test": ("test", "/sdlc:ship"),
    }
    assert all(cards[n]["problems"] == [] for n in got), "every file read"


@pytest.mark.portable
def test_a_file_that_wont_read_needs_the_person_at_any_stage(repo) -> None:
    """086: a stage never hides a problem."""
    folder = _escalated(repo, "026-bad-shipped", "shipped", commit=["src/e.py"])
    _write(folder / "decision.md", "Ship it, I think.\n")
    card = _cards(repo)["026-bad-shipped"]
    assert card["column"] == "needs-you"
    assert any("decision.md" in p for p in card["problems"]), card["problems"]


@pytest.mark.portable
def test_a_restarted_factory_card_is_in_build_with_its_old_decision_as_a_file(served) -> None:
    """095 R11: a change the factory took back has no decision of its own run yet; its old one is
    a file in its folder, never the card's decision."""
    root, url, _ = served
    folder = _change(root, "016-draft-restart", 2, "build", "Draft restart")
    _write(folder / "runs" / "builder.sessions", "s-1\ns-2\n")
    _write(folder / "build" / "round-1.md", "Built.\n")
    _write(folder / "reviews" / "round-1" / "code.md", "VERDICT: PASS\n")
    _write(folder / "decision-1.md", "DECISION: ESCALATE\n\nD1 is still assumed.\n")
    _write(folder / "build" / "round-2.restart.md", "RESTART: decision-1.md\n")
    card = _cards(root)["016-draft-restart"]
    assert (card["column"], card["decision"], card["problems"]) == ("build", None, [])
    assert card["built"] == [1], "the restart record is no builder report"
    assert {"decision-1.md", "build/round-2.restart.md"} <= set(card["files"])
    code, body, _ = _get(f"{url}/file?change=016-draft-restart&path=decision-1.md")
    assert code == 200 and body.startswith(b"DECISION: ESCALATE")


# ---------------------------------------------------------------- the board as it is (098)


@pytest.mark.portable
def test_a_card_with_a_problem_never_names_close(repo) -> None:
    """2026-11-17-23: a card with a file that won't read is under Needs you at any stage, and its
    next step is the problem, never `/sdlc:close`, `/sdlc:ship` or the stage's own step."""
    named = {"026-bad-shipped": "shipped", "028-bad-dropped": "dropped",
             "030-bad-build": "build", "031-bad-test": "test", "032-bad-plan": "plan"}  # fmt: skip
    for name, stage in named.items():
        folder = _escalated(repo, name, stage, commit=[f"src/{name}.py"])
        _write(folder / "decision.md", "Ship it, I think.\n")
    cards = _cards(repo)
    for name in named:
        card = cards[name]
        assert card["column"] == "needs-you" and card["problems"], card
        assert "/sdlc:close" not in card["next"], card["next"]
        assert card["next"] == "fix what its problems name"


# `next_action()`'s precedence, highest first: each state's fields, and the step it names when
# it is the highest a card holds. A card in two states names the higher one's step, whatever
# else it holds; two states that set `stage` to different values can't overlap.
PRECEDENCE = [
    ("rebasing", {"rebasing": True},
     "a rebase is stopped in its worktree: resolve its conflicts, then "
     "sdlc.py resolve 016 --continue, or sdlc.py resolve 016 --abort"),
    ("stage missing", {"stage": None, "problems": ["intent.md couldn't be read: conflict"]},
     "fix intent.md's frontmatter"),
    ("problems", {"problems": ["findings.md couldn't be read: conflict"]},
     "fix what its problems name"),
    ("closed", {"stage": "shipped"}, "/sdlc:close 016"),
    ("stopped", {"stopped": {"next": "read runs/step.md, then rerun the build"}},
     "read runs/step.md, then rerun the build"),
    ("decision pending", {"stage": "build", "pending": ["D1"]},
     "answer its decision in the factory's supervisor"),
    ("approver decided", {"stage": "test", "decision": "READY"},
     "/sdlc:ship, or /sdlc-factory:land with the others ready"),
    ("factory building", {"stage": "build", "mode": "factory", "built": [1]},
     "the factory is building it: wait for its decision"),
    ("red gate", {"gate": {"current": True, "verdict": "FAIL"}},
     "the gate is red: read build/gate.md, fix it, then sdlc.py gate 016"),
    ("its stage's step", {}, "plan mode, then build it"),
]  # fmt: skip


def _in_states(*states: dict) -> dict | None:
    """A card holding every state in `states`, or None when two set different stages."""
    entry = {"id": "016", "tier": 1, "stage": "plan", "mode": "manual", "problems": []}
    stages = {fields["stage"] for fields in states if "stage" in fields}
    if len(stages) > 1:
        return None
    for fields in states:
        for key, value in fields.items():
            entry[key] = entry[key] + value if key == "problems" else value
    return entry


@pytest.mark.portable
@pytest.mark.parametrize(
    "high, low",
    [(PRECEDENCE[i], PRECEDENCE[j]) for i in range(len(PRECEDENCE))
     for j in range(i, len(PRECEDENCE))],
    ids=lambda s: s[0],
)  # fmt: skip
def test_a_card_in_two_states_names_the_higher_ones_step(high, low) -> None:
    """Rounds 1 and 2 of 098 each found one more pair of states `next_action()` put in the
    wrong order: every pair that can overlap is pinned here, by the full text of its step."""
    entry = _in_states(high[1], low[1])
    if entry is None:
        pytest.skip(f"{high[0]} and {low[0]} set different stages")
    assert board.next_action(entry) == high[2]


@pytest.mark.portable
def test_a_decision_counts_on_the_track_only_at_its_stage(repo) -> None:
    """Nit 2026-11-17-22: a change put back to `build` with its `decision.md` still there shows
    the step its record names, not every step done; at `test` the decision is the run's end."""
    folder = _run_at(repo, "review")
    _write(folder / "decision.md", "DECISION: ESCALATE\n\nAsk them.\n")
    assert _states(_cards(repo)["016-draft-tags"]) == TRACKS["review"]
    intent = folder / "intent.md"
    intent.write_text(intent.read_text(encoding="utf-8").replace("stage: build", "stage: test"),
                      encoding="utf-8", newline="\n")  # fmt: skip
    assert _states(_cards(repo)["016-draft-tags"]) == ["done"] * 6


@pytest.mark.portable
def test_board_on_port_0_prints_the_port_it_bound(repo, capsys, monkeypatch) -> None:
    """The board half of 2026-11-17-19: the URL names the port the OS picked, never `:0`."""

    def stop(self, *args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(board._Server, "serve_forever", stop)
    assert board.cmd_board(repo, 0) == 0
    url = json.loads(capsys.readouterr().out)["url"]
    port = int(url.rstrip("/").rsplit(":", 1)[1])
    assert port > 0 and url == f"http://127.0.0.1:{port}/"


def test_a_change_being_rebased_keeps_its_card(repo) -> None:
    """2026-11-17-30: while a rebase stops in a change's worktree its HEAD is detached; the card
    stays, marked rebasing, its branch read from the rebase's own record, and reading it changes
    nothing in git."""
    name = "029-draft-rebase"
    folder = _worktree(repo, name, 1, "plan", commit=["src/rebase.py"])
    tree = sdlc.checkout_of(folder)
    _write(repo / "src" / "rebase.py", "main's own\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main moves")
    stopped = subprocess.run(["git", "-C", str(tree), "rebase", "main"], capture_output=True,
                             encoding="utf-8")  # fmt: skip
    assert stopped.returncode != 0 and _git(tree, "branch", "--show-current") == ""
    before = (_git(tree, "status", "--porcelain"), _git(tree, "rev-parse", "HEAD"))
    card = _cards(repo)[name]
    assert card["rebasing"] is True and card["problems"] == [], card
    assert card["next"] == (
        "a rebase is stopped in its worktree: resolve its conflicts, then "
        "sdlc.py resolve 029 --continue, or sdlc.py resolve 029 --abort"
    ), "never ship or build mid-rebase"
    assert _cards(repo)["001-reopen-drafts"]["rebasing"] is False
    assert name in [p.name for p in sdlc.change_dirs(repo)], "status finds it too"
    assert (_git(tree, "status", "--porcelain"), _git(tree, "rev-parse", "HEAD")) == before
    assert _git(tree, "branch", "--show-current") == "", "the rebase is still under way"
    _git(tree, "rebase", "--abort")
    assert _cards(repo)[name]["rebasing"] is False


@pytest.mark.portable
def test_the_rebasing_badge_is_built_as_text() -> None:
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert re.search(
        r'c\.rebasing\s*\?\s*h\("span", \{ class: "badge rebasing" \}, "rebasing"\)', page
    )


def _touch_later(path: Path, text: str) -> None:
    """Write `path` and move its mtime on, so a filesystem with coarse times still sees a change."""
    before = path.stat().st_mtime_ns
    path.write_text(text, encoding="utf-8", newline="\n")
    later = max(before, path.stat().st_mtime_ns) + 2_000_000_000
    os.utime(path, ns=(later, later))


@pytest.mark.portable
def test_the_running_board_serves_board_py_as_it_is_on_disk(repo, tmp_path) -> None:
    """2026-11-17-47: a change to `board.py` reaches a board already running, with no restart;
    a `board.py` that won't load keeps the code it had, and the state says so."""
    scripts = tmp_path / "plugin" / "scripts"
    scripts.mkdir(parents=True)
    for name in ("board.py", "board.html"):
        (scripts / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    source = scripts / "board.py"
    original = source.read_text(encoding="utf-8")
    copy = board._load(source)
    server = copy.serve(repo, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/state.json"
    try:
        st = json.loads(_get(url)[1])
        assert "patched" not in st and "reload_error" not in st
        patch = (
            "\n_unpatched = state\n\n\n"
            "def state(root):\n    return _unpatched(root) | {'patched': True}\n"
        )
        _touch_later(source, original + patch)
        st = json.loads(_get(url)[1])
        assert st["patched"] is True and len(st["changes"]) == 4, "the edit is served"
        _touch_later(source, original[: len(original) // 2])
        code, body, _ = _get(url)
        st = json.loads(body)
        assert code == 200 and st["patched"] is True, "half a file: the old code serves on"
        assert "board.py" in st["reload_error"]
        assert "restart" not in st["reload_error"], "the next edit that loads is served"
        _touch_later(source, original)
        st = json.loads(_get(url)[1])
        assert "patched" not in st and "reload_error" not in st
        assert _get(url.replace("/state.json", "/"))[0] == 200
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.portable
def test_a_board_that_wont_reload_says_so_on_the_page() -> None:
    page = (ROOT / "scripts" / "board.html").read_text(encoding="utf-8")
    assert re.search(r"st\.reload_error\s*\?", page)
