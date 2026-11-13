"""What `status` puts forward once the open changes are done: `next_up()` over the main checkout's
ideas, nits and direction doc, in NEXT_RULES' order, and the `■ Next up` section that prints it."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from datetime import date
from pathlib import Path

import pytest

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


def _seed(day: str, title: str, tag: str = "idea", after: str = "") -> str:
    line = f"\nAfter: {after}\n" if after else ""
    return f"## [{day}-1] [{tag}] {title}\n\nWhy it's worth doing.\n{line}\n"


def _ideas(root: Path, *seeds: str) -> None:
    _write(root, ".sdlc/work/inbox.md", "# Ideas\n\nSeeds, not a backlog.\n\n" + "".join(seeds))


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
        f".sdlc/work/{name}/intent.md",
        f"---\nid: {nid}\nslug: {slug}\ntier: 1\nimpact: patch\nstage: shipped\n"
        f'created: 2026-10-01\nupdated: 2026-10-01\nidea: "{idea}"\n---\n\n# {nid} — {slug}\n',
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", f"ship {name}")
    _git(root, "rm", "-r", "-q", f".sdlc/work/{name}")
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
    assert _next(root) == {
        "items": [], "done_milestones": [], "warnings": [], "themes": [], "waiting": 0,
        "themeless": 0, "all": [],
    }  # fmt: skip
    assert "Next up" not in _status(root, capsys, monkeypatch)


def test_each_register_alone_is_enough(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _ideas(root, _seed("2026-10-01", "Reopen drafts"))
    assert [i["rule"] for i in _next(root)["items"]] == ["idea"]

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
    intent = (
        root / ".claude" / "worktrees" / "001-share-drafts" / ".sdlc" / "work" / "001-share-drafts"
    )
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


def test_a_mistyped_after_title_warns_and_is_never_next_in_series(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _close(root, "001-reopen-drafts", "Reopen drafts")
    _ideas(root, _seed("2026-10-02", "Share drafts", after='"Reopen draft"'))
    [item] = _next(root)["items"]
    assert (item["rule"], item["label"]) == ("idea", "idea")
    assert _next(root)["warnings"] == [
        '"Share drafts" waits on "Reopen draft", which is no seed or change'
    ]


def test_a_seed_whose_after_seed_is_being_built_is_ready_but_not_yet_in_series(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Reopen drafts", tag="building"),
        _seed("2026-10-02", "Share drafts", after='"Reopen drafts"'),
    )
    assert [(i["rule"], i["title"]) for i in _next(root)["items"]] == [("idea", "Share drafts")]


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
        ("idea", "Plain seed"),
    ]
    assert items[2]["label"] == "M1 (Drafts reopen)"
    # No `Priority:` or `Theme:` line anywhere: the order is today's, and nothing has a theme
    # but the nits.
    assert [i["theme"] for i in items] == [None, None, None, None, "style", None]


@pytest.mark.parametrize("tag", ["idea", "seed"])
def test_milestones_put_forward_their_first_ready_seed_in_doc_order(
    tmp_path: Path, tag: str
) -> None:
    """An older `[seed]` entry is put forward exactly as an `[idea]` is."""
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Older seed", tag),
        _seed("2026-10-02", "Second in M2", tag),
        _seed("2026-10-03", "First in M2", tag),
        _seed("2026-10-04", "Only in M1", tag),
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
        ("idea", "Older seed"),
        ("idea", "Second in M2"),
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


@pytest.mark.portable
def test_status_prints_ten_then_counts_the_rest(tmp_path: Path, capsys, monkeypatch) -> None:
    root = _repo(tmp_path)
    _ideas(root, *(_seed(f"2026-10-{n:02}", f"Seed number {n}") for n in range(1, 13)))
    out = _status(root, capsys, monkeypatch)
    section = out.split("■ Next up: 12\n", 1)[1].split("\n\n", 1)[0].splitlines()
    assert section[10] == "    (+2 more: status --all)"
    assert section[0].startswith("    idea  Seed number 1  (")
    assert section[0].endswith("→ /sdlc:intent 2026-10-01-1")
    assert section[11] == "    Themes:"
    assert section[12].startswith("      (no theme)  12 (12 ideas), oldest ")
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


def test_a_loop_through_a_later_after_title_is_warned(tmp_path: Path) -> None:
    """Sync drafts waits first on Print drafts, which waits on a seed in no loop; the loop runs
    through its second title."""
    root = _repo(tmp_path)
    _ideas(
        root,
        _seed("2026-10-01", "Sync drafts", after='"Print drafts", "Merge drafts"'),
        _seed("2026-10-02", "Print drafts", after='"Plain seed"'),
        _seed("2026-10-03", "Merge drafts", after='"Sync drafts"'),
        _seed("2026-10-04", "Plain seed"),
    )
    assert _next(root)["warnings"] == [
        'these seeds wait on each other, so none will come up: "Sync drafts", "Merge drafts"',
    ]


def _entry(day: str, title: str, tag: str = "idea", *lines: str) -> str:
    body = "".join(f"{line}\n" for line in lines)
    return f"## [{day}-1] [{tag}] {title}\n\nWhy it's worth doing.\n{body}\n"


@pytest.mark.portable
def test_priority_reads_high_med_low_and_reports_a_bad_word(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _ideas(
        root,
        _entry("2026-10-01", "Reopen drafts", "idea", "Priority: High"),
        _entry("2026-10-02", "Share drafts", "idea", "Priority: urgent"),
        _entry("2026-10-03", "Sync drafts", "idea", "Priority: med"),
        _nit("004-1", "style", "2026-10-04").replace("low\n", "low\nPriority: high\n"),
    )
    got = {e["title"]: sdlc.entry_priority(e) for e in sdlc.inbox_entries(root)}
    assert got["Reopen drafts"] == "high" and got["Sync drafts"] == "med"
    problems = [p["detail"] for p in sdlc.analyze(root)["problems"] if p["kind"] == "priority"]
    assert problems == [
        "2026-10-02-1: Priority must be one of high|med|low, got 'urgent'",
        "2026-10-04-1: a nit has no Priority: its Cost: and Value: rank it",
    ]


@pytest.mark.portable
def test_priority_high_ranks_first_and_low_last(tmp_path: Path) -> None:
    """High comes before every rule, a high bug by severity before a high idea, low after every
    rule, and a high seed a milestone also groups comes up once, as high."""
    root = _repo(tmp_path)
    _ideas(
        root,
        _entry("2026-10-01", "Plain seed"),
        _entry("2026-10-02", "Ignored seed", "idea", "Priority: low"),
        _entry("2026-10-03", "Grouped seed"),
        _entry("2026-10-04", "Grouped urgent seed", "idea", "Priority: high"),
        _entry("2026-10-05", "Drafts lose their title", "bug", "Severity: high"),
        _entry("2026-10-06", "Urgent idea", "idea", "Priority: high"),
        _entry("2026-10-07", "Urgent bug", "bug", "Severity: low", "Priority: high"),
        _entry("2026-10-08", "Plain seed with med", "idea", "Priority: med"),
    )
    _direction(root, _milestone("M1", "Drafts reopen", '"Grouped urgent seed", "Grouped seed"'))
    items = _next(root)["items"]
    assert [(i["rule"], i["title"]) for i in items] == [
        ("priority", "Urgent bug"),
        ("priority", "Grouped urgent seed"),
        ("priority", "Urgent idea"),
        ("bug", "Drafts lose their title"),
        ("milestone", "Grouped seed"),
        ("idea", "Plain seed"),
        ("idea", "Plain seed with med"),
        ("low", "Ignored seed"),
    ]
    assert items[0]["label"] == "priority high · bug low"
    assert items[-1]["label"] == "priority low · idea"


@pytest.mark.portable
def test_themes_count_every_open_entry_by_kind_best_ranked_first(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """A theme groups ideas, bugs and nits of any cost; themes come in the order of their best
    line, one with no line after those with one, and the entries with no theme last."""
    root = _repo(tmp_path)
    _ideas(
        root,
        _entry("2026-10-01", "Plain seed"),
        _entry("2026-10-02", "Share drafts", "idea", "Theme: drafts"),
        _entry("2026-10-03", "Drafts lose their title", "bug", "Severity: high", "Theme: drafts"),
        _nit("004-1", "drafts", "2026-10-04", cost="M"),
        _nit("005-1", "style", "2026-10-05", cost="M"),
        _nit("006-1", "tests", "2026-10-06"),
    )
    nxt = _next(root)
    assert [i["theme"] for i in nxt["items"]] == ["drafts", "tests", None, "drafts"]
    assert [(t["theme"], t["counts"]) for t in nxt["themes"]] == [
        ("drafts", {"idea": 1, "bug": 1, "nit": 1}),
        ("tests", {"nit": 1}),
        ("style", {"nit": 1}),
        ("(no theme)", {"idea": 1}),
    ]
    out = _status(root, capsys, monkeypatch)
    assert "    bug high  [drafts] Drafts lose their title  (" in out
    assert "      drafts  3 (1 bug, 1 idea, 1 nit), oldest " in out


@pytest.mark.portable
def test_status_all_lists_every_candidate_once_by_theme(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    _ideas(
        root,
        *(_entry(f"2026-10-{n:02}", f"Seed number {n}") for n in range(1, 13)),
        _entry("2026-10-13", "Share drafts", "idea", "Theme: drafts"),
        _nit("004-1", "drafts", "2026-10-14", cost="M"),
    )
    groups = _next(root)["all"]
    assert [g["theme"] for g in groups] == ["drafts", "(no theme)"]
    titles = [i["title"] for g in groups for i in g["items"]]
    assert len(titles) == len(set(titles)) == 14
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["sdlc.py", "status", "--all"])
    sdlc.main()
    out = capsys.readouterr().out
    assert "    drafts\n      idea  Share drafts  (" in out
    assert "      nit M  A small thing in drafts  (" in out
    assert "more: status --all" not in out
    assert all(f"  Seed number {n}  (" in out for n in range(1, 13))


@pytest.mark.portable
def test_open_change_shows_when_it_was_last_touched(tmp_path: Path, capsys, monkeypatch) -> None:
    """From the newest of its own commits and its worktree's changed files: quiet after a day."""
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "share-drafts", 1, None, worktree=True) == 0
    tree = root / ".claude" / "worktrees" / "001-share-drafts"
    old = sdlc.datetime.now(sdlc.UTC).timestamp() - 2 * 24 * 3600
    for rel in sdlc._dirty_paths(tree):
        os.utime(tree / rel, (old, old))
    capsys.readouterr()

    def line() -> str:
        out = _status(root, capsys, monkeypatch).splitlines()
        return next(x for x in out if x.startswith("    001  "))

    assert line().endswith("· quiet, touched 2d ago")
    (tree / ".sdlc" / "work" / "001-share-drafts" / "notes.md").write_text("x\n", encoding="utf-8")
    assert line().endswith("· touched 0m ago")


@pytest.mark.portable
def test_a_folder_in_the_main_checkout_is_touched_only_by_its_own_files(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    root = _repo(tmp_path)
    assert sdlc.cmd_new(root, "share-drafts", 1, None) == 0
    old = sdlc.datetime.now(sdlc.UTC).timestamp() - 2 * 24 * 3600
    for rel in sdlc._dirty_paths(root):
        os.utime(root / rel, (old, old))
    (root / "README.md").write_text("an unrelated edit\n", encoding="utf-8")
    capsys.readouterr()
    out = _status(root, capsys, monkeypatch).splitlines()
    assert next(x for x in out if x.startswith("    001  ")).endswith("· quiet, touched 2d ago")


NUDGE = "ideas and bugs have no theme: /sdlc:idea --themes proposes them"


@pytest.mark.portable
def test_status_points_at_the_themes_pass_from_five_themeless(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """Ideas and bugs without a theme count, waiting ones too; a themed one, a nit or a seed
    being built never does."""
    root = _repo(tmp_path)
    four = [
        _entry("2026-10-01", "Reopen drafts"),
        _entry("2026-10-02", "Share drafts", "idea", 'After: "Reopen drafts"'),
        _entry("2026-10-03", "Drafts lose their title", "bug", "Severity: high"),
        _entry("2026-10-04", "Sync drafts"),
        _entry("2026-10-05", "Merge drafts", "idea", "Theme: drafts"),
        _entry("2026-10-06", "Rename drafts", "building"),
        _nit("004-1", "style", "2026-10-07"),
    ]
    _ideas(root, *four)
    assert _next(root)["themeless"] == 4
    assert NUDGE not in _status(root, capsys, monkeypatch)
    _ideas(root, *four, _entry("2026-10-08", "Print drafts"))
    out = _status(root, capsys, monkeypatch)
    assert f"    5 {NUDGE}\n" in out
    # The same five, the waiting seed among them, as Themes: counts them.
    assert "      (no theme)  5 (1 bug, 4 ideas), oldest " in out


@pytest.mark.portable
def test_inbox_commit_records_a_themes_pass_as_one_update(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    plain = [
        _entry("2026-10-01", "Reopen drafts"),
        _entry("2026-10-02", "Drafts lose their title", "bug", "Severity: high"),
        _entry("2026-10-03", "Share drafts"),
        _entry("2026-10-04", "Sync drafts"),
    ]
    _ideas(root, *plain)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seeds")
    themed = [e.replace("doing.\n", "doing.\nTheme: drafts\n", 1) for e in plain[:3]]
    _ideas(root, *themed, plain[3])
    assert sdlc.cmd_inbox_commit(root) == 0, capsys.readouterr().out
    assert _git(root, "log", "-1", "--format=%s") == (
        "Update 2026-10-01-1, 2026-10-02-1, 2026-10-03-1"
    )
    diff = _git(root, "show", "--format=", "-U0", "HEAD").splitlines()
    assert [d for d in diff if d[:1] in "+-" and d[:3] not in ("+++", "---")] == [
        "+Theme: drafts"
    ] * 3
    assert _git(root, "status", "--short") == ""
