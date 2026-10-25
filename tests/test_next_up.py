"""What `status` puts forward once the open changes are done: `next_up()` over the main checkout's
ideas, nits and direction doc, in NEXT_RULES' order, and the `■ Next up` section that prints it."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("sdlc_next_up", ROOT / "scripts" / "sdlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sdlc = _load()
TODAY = date(2026, 10, 25)


def _git(root: Path, *args: str) -> str:
    env = os.environ | {"GIT_COMMITTER_DATE": "2026-10-20T12:00:00"}
    out = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return out.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    (root / ".gitignore").write_text(".claude/worktrees/\n", encoding="utf-8")
    (root / "README.md").write_text("a repo\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed(day: str, title: str, tag: str = "seed", after: str = "") -> str:
    line = f"\nAfter: {after}\n" if after else ""
    return f"## [{day}] [{tag}] {title}\n\nWhy it's worth doing.\n{line}\n"


def _ideas(root: Path, *seeds: str) -> None:
    _write(root, "work/inbox.md", "# Ideas\n\nSeeds, not a backlog.\n\n" + "".join(seeds))


def _nit(nid: str, theme: str, raised: str, cost: str = "S") -> str:
    return (
        f"## [{raised}-{nid.split('-')[1]}] [nit] A small thing in {theme}\n\n"
        f"Theme: {theme}\nPaths: `scripts/drafts.py`\nCost: {cost}\nValue: low\n"
        f"Raised by: {nid.split('-')[0]}-reopen-drafts (correctness)\n\n"
    )


def _direction(root: Path, *milestones: str) -> None:
    _write(root, ".sdlc/DIRECTION.md", "# Direction\n\n## Milestones\n\n" + "".join(milestones))


def _milestone(mid: str, title: str, groups: str) -> str:
    return f"### {mid}. {title}\n\nWhat's true when it's done.\n\nGroups: {groups}\n\n"


def _next(root: Path, open_changes: list[dict] | None = None) -> dict:
    return sdlc.next_up(root, sdlc.load_config(root)[0], open_changes or [], TODAY)


def _status(root: Path, capsys, monkeypatch) -> str:
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status"])
    sdlc.main()
    return capsys.readouterr().out


def _close(root: Path, name: str, idea: str) -> None:
    """A change whose intent names `idea`, shipped and then closed on main."""
    nid, slug = name.split("-", 1)
    _write(
        root,
        f"work/{name}/intent.md",
        f"---\nid: {nid}\nslug: {slug}\ntier: 1\nimpact: patch\nstage: shipped\n"
        f'created: 2026-10-01\nupdated: 2026-10-01\nidea: "{idea}"\n---\n\n# {nid} — {slug}\n',
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"ship {name}")
    _git(root, "rm", "-r", "-q", f"work/{name}")
    _git(root, "commit", "-q", "-m", f"Close {name}")


def test_idea_entries_reads_after_lines(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Reopen drafts"),
        _seed("2026-10-02", "Share drafts", after='"Reopen drafts"'),
        _seed("2026-10-03", "Sync drafts", after='"Reopen drafts", "Share drafts"'),
    )
    got = {e["title"]: e["after"] for e in sdlc.inbox_entries(root)}
    assert got == {
        "Reopen drafts": [],
        "Share drafts": ["Reopen drafts"],
        "Sync drafts": ["Reopen drafts", "Share drafts"],
    }


def test_next_up_is_empty_without_registers(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    assert _next(root) == {"items": [], "done_milestones": [], "warnings": []}
    assert "Next up" not in _status(root, capsys, monkeypatch)


def test_each_register_alone_is_enough(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _ideas(root, _seed("2026-10-01", "Reopen drafts"))
    assert [i["rule"] for i in _next(root)["items"]] == ["seed"]

    root = _repo(tmp_path / "nits")
    _ideas(root, _nit("003-1", "style", "2026-10-04"))
    assert [i["rule"] for i in _next(root)["items"]] == ["nits"]

    # A milestone whose grouped seed isn't in the register puts nothing forward.
    root = _repo(tmp_path / "direction")
    _direction(root, _milestone("M1", "Drafts reopen", '"Reopen drafts"'))
    assert _next(root)["items"] == []


def test_next_up_skips_a_seed_an_open_change_builds(tmp_path: Path) -> None:
    """Tagged `[building]`, or named by a change open in a worktree while main still says
    `[seed]`: the branch tags its seed, main's register hasn't heard yet."""
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Reopen drafts", tag="building"),
        _seed("2026-10-02", "Share drafts"),
        _seed("2026-10-03", "Sync drafts"),
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seeds")
    assert sdlc.cmd_new(root, "share-drafts", 1, None, worktree=True) == 0
    intent = root / ".claude" / "worktrees" / "001-share-drafts" / "work" / "001-share-drafts"
    text = (intent / "intent.md").read_text(encoding="utf-8")
    (intent / "intent.md").write_text(
        text.replace("idea:\n", 'idea: "Share drafts"\n', 1), encoding="utf-8"
    )
    open_changes = sdlc.analyze(root)["open"]
    assert [i["title"] for i in _next(root, open_changes)["items"]] == ["Sync drafts"]


def test_a_seed_waits_while_its_after_seed_is_open(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    first = _seed("2026-10-01", "Reopen drafts")
    second = _seed("2026-10-02", "Share drafts", after='"Reopen drafts"')
    _ideas(root, first, second)
    assert [i["title"] for i in _next(root)["items"]] == ["Reopen drafts"]

    # The first phase shipped, so its entry left the register: the second is next in its series.
    _close(root, "001-reopen-drafts", "Reopen drafts")
    _ideas(root, second)
    [item] = _next(root)["items"]
    assert item["rule"] == "series" and item["label"] == 'next in series after "Reopen drafts"'
    assert _next(root)["warnings"] == []


def test_a_seed_whose_after_seed_is_being_built_is_ready_but_not_yet_in_series(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Reopen drafts", tag="building"),
        _seed("2026-10-02", "Share drafts", after='"Reopen drafts"'),
    )
    assert [(i["rule"], i["title"]) for i in _next(root)["items"]] == [("seed", "Share drafts")]


def test_next_up_orders_by_rule(tmp_path: Path) -> None:
    """One candidate per rule, written in reverse order, plus a bug a milestone also groups: it
    comes up once, as a bug."""
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", "Reopen drafts")
    _ideas(
        root,
        _seed("2026-10-01", "Plain seed"),
        _seed("2026-10-02", "Share drafts", after='"Reopen drafts"'),
        _seed("2026-10-03", "Grouped seed"),
        _seed("2026-10-04", "Drafts lose their title", tag="bug"),
        _seed("2026-10-05", "Grouped bug", tag="bug"),
        _nit("003-1", "style", "2026-10-04"),
    )
    _direction(
        root,
        _milestone("M1", "Drafts reopen", '"Grouped bug", "Grouped seed"'),
    )
    items = _next(root)["items"]
    assert [(i["rule"], i["title"]) for i in items] == [
        ("bug", "Drafts lose their title"),
        ("bug", "Grouped bug"),
        ("milestone", "Grouped seed"),
        ("series", "Share drafts"),
        ("nits", "[style] 1 open, cost S"),
        ("seed", "Plain seed"),
    ]
    assert items[2]["label"] == "M1 (Drafts reopen)"


def test_milestones_put_forward_their_first_ready_seed_in_doc_order(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Older seed"),
        _seed("2026-10-02", "Second in M2"),
        _seed("2026-10-03", "First in M2"),
        _seed("2026-10-04", "Only in M1"),
    )
    _direction(
        root,
        _milestone("M1", "First goal", '"Only in M1"'),
        _milestone("M2", "Second goal", '"First in M2", "Second in M2"'),
    )
    got = [(i["rule"], i["title"]) for i in _next(root)["items"]]
    assert got == [
        ("milestone", "Only in M1"),
        ("milestone", "First in M2"),
        ("seed", "Older seed"),
        ("seed", "Second in M2"),
    ]


def test_nits_of_cost_s_come_one_line_per_theme_oldest_first(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    nits = (
        _nit("003-1", "style", "2026-10-10")
        + _nit("003-2", "style", "2026-10-12")
        + _nit("004-1", "robustness", "2026-10-05")
        + _nit("004-2", "tests", "2026-10-01", cost="M")
    )
    _ideas(root, nits)
    items = _next(root)["items"]
    assert [i["title"] for i in items] == ["[robustness] 1 open, cost S", "[style] 2 open, cost S"]
    assert items[0]["command"] == "/sdlc:intent pay down the [robustness] nits"
    assert items[0]["age_days"] == 20


def test_status_prints_five_then_counts_the_rest(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    _ideas(root, *(_seed(f"2026-10-0{n}", f"Seed number {n}") for n in range(1, 8)))
    out = _status(root, capsys, monkeypatch)
    section = out.split("■ Next up: 7\n", 1)[1].split("\n\n", 1)[0].splitlines()
    assert len(section) == 6 and section[-1] == "    (+2 more)"
    assert section[0].startswith("    seed  Seed number 1  (")
    assert section[0].endswith("→ /sdlc:intent Seed number 1")
    # Before the nudges and the problems, after everything that was there already.
    assert out.index("■ Next up") < out.index("■ Problems")


def test_a_milestone_with_nothing_left_says_so(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", "Reopen drafts")
    _ideas(root, _seed("2026-10-02", "Share drafts"))
    _direction(
        root,
        _milestone("M1", "Drafts reopen", '001, "Reopen drafts"'),
        _milestone("M2", "Drafts are shared", '"Share drafts"'),
    )
    assert _next(root)["done_milestones"] == ["M1"]
    out = _status(root, capsys, monkeypatch)
    assert "    M1 has nothing left in its groups: /sdlc:retro decides whether it's done" in out


def test_after_lines_that_can_never_be_met_warn_and_never_fail_check(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Share drafts", after='"No such seed"'),
        _seed("2026-10-02", "Sync drafts", after='"Merge drafts"'),
        _seed("2026-10-03", "Merge drafts", after='"Sync drafts"'),
    )
    warnings = _next(root)["warnings"]
    assert warnings == [
        '"Share drafts" waits on "No such seed", which is no seed or change',
        'these seeds wait on each other, so none will come up: "Sync drafts", "Merge drafts"',
    ]
    out = _status(root, capsys, monkeypatch)
    assert f"    ⚠  {warnings[1]}" in out
    monkeypatch.setattr("sys.argv", ["sdlc.py", "check", "--strict"])
    assert sdlc.main() == 0
